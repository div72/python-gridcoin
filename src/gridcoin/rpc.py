import functools
import os
from pathlib import Path

from collections.abc import Awaitable, Callable, Sequence
from typing import (
    overload,
    runtime_checkable,
    Any,
    ClassVar,
    Final,
    Generic,
    Optional,
    Protocol,
    TypedDict,
    TypeVar,
    Unpack,
)

JSONValue = (
    str | int | float | dict[str, "JSONValue"] | Sequence["JSONValue"] | bool | None
)

T = TypeVar("T", bound=Awaitable[JSONValue] | JSONValue, covariant=True)


@runtime_checkable
class JSONDeserializable(Protocol[T]):
    def json(self) -> T:
        ...


class JSONParams(TypedDict):
    json: JSONValue


class Postable(Protocol[T]):
    def __call__(
        self, url: str, **kwargs: Unpack[JSONParams]
    ) -> JSONDeserializable[T] | Awaitable[JSONDeserializable[T]]:
        ...


class JSONResponseError(TypedDict):
    code: int
    message: str


class JSONResponse(TypedDict):
    result: JSONValue
    error: Optional[JSONResponseError]


class WalletRPCException(Exception):
    code: int
    exc_types: ClassVar[dict[int, type]] = {}

    def __new__(cls, code: int, *args: Any) -> "WalletRPCException":
        if cls is WalletRPCException:
            try:
                return WalletRPCException.exc_types[code](code, *args)
            except KeyError:
                pass

        return Exception.__new__(cls, code, *args)  # type: ignore

    def __init__(self, code: int, *args: Any):
        self.code = code
        super().__init__(*args)

    def __init_subclass__(cls, code: int, **kwargs: Any):
        WalletRPCException.exc_types[code] = cls
        super().__init_subclass__(**kwargs)


# Generated for Gridcoin 5.4.5.3
class InvalidRequestError(WalletRPCException, code=-32600):
    pass


class MethodNotFoundError(WalletRPCException, code=-32601):
    pass


class InvalidParamsError(WalletRPCException, code=-32602):
    pass


class InternalError(WalletRPCException, code=-32603):
    pass


class ParseError(WalletRPCException, code=-32700):
    pass


class MiscError(WalletRPCException, code=-1):
    pass


class RPCTypeError(WalletRPCException, code=-3):
    pass


class InvalidAddressOrKeyError(WalletRPCException, code=-5):
    pass


class OutOfMemoryError(WalletRPCException, code=-7):
    pass


class InvalidParameterError(WalletRPCException, code=-8):
    pass


class DatabaseError(WalletRPCException, code=-20):
    pass


class DeserializationError(WalletRPCException, code=-22):
    pass


class VerifyError(WalletRPCException, code=-25):
    pass


class VerifyRejectedError(WalletRPCException, code=-26):
    pass


class VerifyAlreadyInChainError(WalletRPCException, code=-27):
    pass


class InWarmupError(WalletRPCException, code=-28):
    pass


class MethodDeprecatedError(WalletRPCException, code=-32):
    pass


class ClientNotConnectedError(WalletRPCException, code=-9):
    pass


class ClientInInitialDownloadError(WalletRPCException, code=-10):
    pass


class ClientNodeAlreadyAddedError(WalletRPCException, code=-23):
    pass


class ClientNodeNotAddedError(WalletRPCException, code=-24):
    pass


class ClientNodeNotConnectedError(WalletRPCException, code=-29):
    pass


class ClientInvalidIpOrSubnetError(WalletRPCException, code=-30):
    pass


class ClientP2pDisabledError(WalletRPCException, code=-31):
    pass


class ClientNodeCapacityReachedError(WalletRPCException, code=-34):
    pass


class ClientMempoolDisabledError(WalletRPCException, code=-33):
    pass


class WalletError(WalletRPCException, code=-4):
    pass


class WalletInsufficientFundsError(WalletRPCException, code=-6):
    pass


class WalletInvalidLabelNameError(WalletRPCException, code=-11):
    pass


class WalletKeypoolRanOutError(WalletRPCException, code=-12):
    pass


class WalletUnlockNeededError(WalletRPCException, code=-13):
    pass


class WalletPassphraseIncorrectError(WalletRPCException, code=-14):
    pass


class WalletWrongEncStateError(WalletRPCException, code=-15):
    pass


class WalletEncryptionFailedError(WalletRPCException, code=-16):
    pass


class WalletAlreadyUnlockedError(WalletRPCException, code=-17):
    pass


class WalletNotFoundError(WalletRPCException, code=-18):
    pass


class WalletNotSpecifiedError(WalletRPCException, code=-19):
    pass


class WalletAlreadyLoadedError(WalletRPCException, code=-35):
    pass


class WalletAlreadyExistsError(WalletRPCException, code=-36):
    pass


class ForbiddenBySafeModeError(WalletRPCException, code=-2):
    pass


def _get_result(resp: JSONDeserializable[T] | Awaitable[JSONDeserializable[T]]) -> T:
    if isinstance(resp, JSONDeserializable):
        ret: JSONResponse = resp.json()  # type: ignore

        if ret["error"] is not None:
            raise WalletRPCException(ret["error"]["code"], ret["error"]["message"])

        return ret["result"]  # type: ignore
    else:

        async def unpacker(o: Awaitable[JSONDeserializable[T]]) -> JSONValue:
            r = await o

            ret: JSONResponse = await r.json()  # type: ignore
            # Keeping pyright happy.
            error: Optional[JSONResponseError] = ret["error"]

            if error is not None:
                raise WalletRPCException(error["code"], error["message"])

            return ret["result"]

        return unpacker(resp)  # type: ignore


class WalletRPC(Generic[T]):
    io_func: Postable[T]
    url: str

    @staticmethod
    def url_from_config(config_file: str | os.PathLike[str]) -> str:
        config_path: Path = Path(config_file)

        data: dict[str, str] = dict(
            filter(
                lambda parts: len(parts) == 2,
                map(
                    lambda line: line.split("#", 1)[0].rstrip().split("=", 1),
                    config_path.read_text().splitlines(),
                ),
            )
        )

        testnet: bool = config_path.parent.name == "testnet"

        port: str = data.get("rpcport", "25715" if testnet else "15715")

        return f"http://{data['rpcuser']}:{data['rpcpassword']}@localhost:{port}"

    def __init__(
        self, io_func: Postable[T], url: Optional[str] = None, testnet: bool = False
    ):
        self.io_func = io_func

        if url is None:
            data_path = Path("~/.GridcoinResearch").expanduser()

            if testnet:
                data_path = data_path / "testnet"

            self.url = WalletRPC.url_from_config(data_path / "gridcoinresearch.conf")
        else:
            self.url = url

    @functools.cache
    def __getattribute__(self, name: str):
        if name in WalletRPC.COMMANDS:

            def _call(*args: JSONValue) -> T:
                return _get_result(
                    self.io_func(self.url, json={"method": name, "params": args})
                )

            return _call

        return super().__getattribute__(name)

    # Generated for Gridcoin 5.4.5

    COMMANDS: Final[frozenset[str]] = frozenset(
        {
            "help",
            "addmultisigaddress",
            "addredeemscript",
            "backupprivatekeys",
            "backupwallet",
            "burn",
            "checkwallet",
            "createrawtransaction",
            "consolidatemsunspent",
            "decoderawtransaction",
            "decodescript",
            "dumpprivkey",
            "dumpwallet",
            "encryptwallet",
            "getaccount",
            "getaccountaddress",
            "getaddressesbyaccount",
            "getbalance",
            "getbalancedetail",
            "getnewaddress",
            "getnewpubkey",
            "getrawtransaction",
            "getrawwallettransaction",
            "getreceivedbyaccount",
            "getreceivedbyaddress",
            "gettransaction",
            "getunconfirmedbalance",
            "getwalletinfo",
            "importprivkey",
            "importwallet",
            "keypoolrefill",
            "listaccounts",
            "listaddressgroupings",
            "listreceivedbyaccount",
            "listreceivedbyaddress",
            "listsinceblock",
            "liststakes",
            "listtransactions",
            "listunspent",
            "consolidateunspent",
            "makekeypair",
            "maintainbackups",
            "move",
            "rainbymagnitude",
            "repairwallet",
            "resendtx",
            "reservebalance",
            "scanforunspent",
            "sendfrom",
            "sendmany",
            "sendrawtransaction",
            "sendtoaddress",
            "setaccount",
            "sethdseed",
            "settxfee",
            "signmessage",
            "signrawtransaction",
            "upgradewallet",
            "validateaddress",
            "validatepubkey",
            "verifymessage",
            "walletlock",
            "walletpassphrase",
            "walletpassphrasechange",
            "walletdiagnose",
            "advertisebeacon",
            "beaconconvergence",
            "beaconreport",
            "beaconstatus",
            "createmrcrequest",
            "explainmagnitude",
            "getlaststake",
            "getmrcinfo",
            "getstakinginfo",
            "getmininginfo",
            "lifetime",
            "magnitude",
            "pendingbeaconreport",
            "resetcpids",
            "revokebeacon",
            "superblockage",
            "superblocks",
            "auditsnapshotaccrual",
            "auditsnapshotaccruals",
            "addkey",
            "changesettings",
            "currentcontractaverage",
            "debug",
            "dumpcontracts",
            "exportstats1",
            "getblockstats",
            "getlistof",
            "getrecentblocks",
            "inspectaccrualsnapshot",
            "listalerts",
            "listdata",
            "listprojects",
            "listresearcheraccounts",
            "listsettings",
            "logging",
            "network",
            "parseaccrualsnapshotfile",
            "parselegacysb",
            "projects",
            "readdata",
            "reorganize",
            "sendalert",
            "sendalert2",
            "sendblock",
            "superblockaverage",
            "versionreport",
            "writedata",
            "listmanifests",
            "getmpart",
            "sendscraperfilemanifest",
            "savescraperfilemanifest",
            "deletecscrapermanifest",
            "archivelog",
            "testnewsb",
            "convergencereport",
            "scraperreport",
            "addnode",
            "askforoutstandingblocks",
            "getblockchaininfo",
            "getnetworkinfo",
            "clearbanned",
            "currenttime",
            "getaddednodeinfo",
            "getnodeaddresses",
            "getbestblockhash",
            "getblock",
            "getblockbynumber",
            "getblockbymintime",
            "getblocksbatch",
            "getblockcount",
            "getblockhash",
            "getburnreport",
            "getcheckpoint",
            "getconnectioncount",
            "getdifficulty",
            "getinfo",
            "getnettotals",
            "getpeerinfo",
            "getrawmempool",
            "listbanned",
            "networktime",
            "ping",
            "setban",
            "showblock",
            "stop",
            "addpoll",
            "getpollresults",
            "getvotingclaim",
            "listpolls",
            "vote",
            "votebyid",
            "votedetails",
        }
    )

    def help(self, *args: Any) -> T:
        ...

    def addmultisigaddress(self, *args: Any) -> T:
        ...

    def addredeemscript(self, *args: Any) -> T:
        ...

    def backupprivatekeys(self, *args: Any) -> T:
        ...

    def backupwallet(self, *args: Any) -> T:
        ...

    def burn(self, *args: Any) -> T:
        ...

    def checkwallet(self, *args: Any) -> T:
        ...

    def createrawtransaction(self, *args: Any) -> T:
        ...

    def consolidatemsunspent(self, *args: Any) -> T:
        ...

    def decoderawtransaction(self, *args: Any) -> T:
        ...

    def decodescript(self, *args: Any) -> T:
        ...

    def dumpprivkey(self, *args: Any) -> T:
        ...

    def dumpwallet(self, *args: Any) -> T:
        ...

    def encryptwallet(self, *args: Any) -> T:
        ...

    def getaccount(self, *args: Any) -> T:
        ...

    def getaccountaddress(self, *args: Any) -> T:
        ...

    def getaddressesbyaccount(self, *args: Any) -> T:
        ...

    def getbalance(self, *args: Any) -> T:
        ...

    def getbalancedetail(self, *args: Any) -> T:
        ...

    def getnewaddress(self, *args: Any) -> T:
        ...

    def getnewpubkey(self, *args: Any) -> T:
        ...

    def getrawtransaction(self, *args: Any) -> T:
        ...

    def getrawwallettransaction(self, *args: Any) -> T:
        ...

    def getreceivedbyaccount(self, *args: Any) -> T:
        ...

    def getreceivedbyaddress(self, *args: Any) -> T:
        ...

    def gettransaction(self, *args: Any) -> T:
        ...

    def getunconfirmedbalance(self, *args: Any) -> T:
        ...

    def getwalletinfo(self, *args: Any) -> T:
        ...

    def importprivkey(self, *args: Any) -> T:
        ...

    def importwallet(self, *args: Any) -> T:
        ...

    def keypoolrefill(self, *args: Any) -> T:
        ...

    def listaccounts(self, *args: Any) -> T:
        ...

    def listaddressgroupings(self, *args: Any) -> T:
        ...

    def listreceivedbyaccount(self, *args: Any) -> T:
        ...

    def listreceivedbyaddress(self, *args: Any) -> T:
        ...

    def listsinceblock(self, *args: Any) -> T:
        ...

    def liststakes(self, *args: Any) -> T:
        ...

    def listtransactions(self, *args: Any) -> T:
        ...

    def listunspent(self, *args: Any) -> T:
        ...

    def consolidateunspent(self, *args: Any) -> T:
        ...

    def makekeypair(self, *args: Any) -> T:
        ...

    def maintainbackups(self, *args: Any) -> T:
        ...

    def move(self, *args: Any) -> T:
        ...

    def rainbymagnitude(self, *args: Any) -> T:
        ...

    def repairwallet(self, *args: Any) -> T:
        ...

    def resendtx(self, *args: Any) -> T:
        ...

    def reservebalance(self, *args: Any) -> T:
        ...

    def scanforunspent(self, *args: Any) -> T:
        ...

    def sendfrom(self, *args: Any) -> T:
        ...

    def sendmany(self, *args: Any) -> T:
        ...

    def sendrawtransaction(self, *args: Any) -> T:
        ...

    def sendtoaddress(self, *args: Any) -> T:
        ...

    def setaccount(self, *args: Any) -> T:
        ...

    def sethdseed(self, *args: Any) -> T:
        ...

    def settxfee(self, *args: Any) -> T:
        ...

    def signmessage(self, *args: Any) -> T:
        ...

    def signrawtransaction(self, *args: Any) -> T:
        ...

    def upgradewallet(self, *args: Any) -> T:
        ...

    def validateaddress(self, *args: Any) -> T:
        ...

    def validatepubkey(self, *args: Any) -> T:
        ...

    def verifymessage(self, *args: Any) -> T:
        ...

    def walletlock(self, *args: Any) -> T:
        ...

    def walletpassphrase(self, *args: Any) -> T:
        ...

    def walletpassphrasechange(self, *args: Any) -> T:
        ...

    def walletdiagnose(self, *args: Any) -> T:
        ...

    def advertisebeacon(self, *args: Any) -> T:
        ...

    def beaconconvergence(self, *args: Any) -> T:
        ...

    def beaconreport(self, *args: Any) -> T:
        ...

    def beaconstatus(self, *args: Any) -> T:
        ...

    def createmrcrequest(self, *args: Any) -> T:
        ...

    def explainmagnitude(self, *args: Any) -> T:
        ...

    def getlaststake(self, *args: Any) -> T:
        ...

    def getmrcinfo(self, *args: Any) -> T:
        ...

    def getstakinginfo(self, *args: Any) -> T:
        ...

    def getmininginfo(self, *args: Any) -> T:
        ...

    def lifetime(self, *args: Any) -> T:
        ...

    def magnitude(self, *args: Any) -> T:
        ...

    def pendingbeaconreport(self, *args: Any) -> T:
        ...

    def resetcpids(self, *args: Any) -> T:
        ...

    def revokebeacon(self, *args: Any) -> T:
        ...

    def superblockage(self, *args: Any) -> T:
        ...

    def superblocks(self, *args: Any) -> T:
        ...

    def auditsnapshotaccrual(self, *args: Any) -> T:
        ...

    def auditsnapshotaccruals(self, *args: Any) -> T:
        ...

    def addkey(self, *args: Any) -> T:
        ...

    def changesettings(self, *args: Any) -> T:
        ...

    def currentcontractaverage(self, *args: Any) -> T:
        ...

    def debug(self, *args: Any) -> T:
        ...

    def dumpcontracts(self, *args: Any) -> T:
        ...

    def exportstats1(self, *args: Any) -> T:
        ...

    def getblockstats(self, *args: Any) -> T:
        ...

    def getlistof(self, *args: Any) -> T:
        ...

    def getrecentblocks(self, *args: Any) -> T:
        ...

    def inspectaccrualsnapshot(self, *args: Any) -> T:
        ...

    def listalerts(self, *args: Any) -> T:
        ...

    def listdata(self, *args: Any) -> T:
        ...

    def listprojects(self, *args: Any) -> T:
        ...

    def listresearcheraccounts(self, *args: Any) -> T:
        ...

    def listsettings(self, *args: Any) -> T:
        ...

    def logging(self, *args: Any) -> T:
        ...

    def network(self, *args: Any) -> T:
        ...

    def parseaccrualsnapshotfile(self, *args: Any) -> T:
        ...

    def parselegacysb(self, *args: Any) -> T:
        ...

    def projects(self, *args: Any) -> T:
        ...

    def readdata(self, *args: Any) -> T:
        ...

    def reorganize(self, *args: Any) -> T:
        ...

    def sendalert(self, *args: Any) -> T:
        ...

    def sendalert2(self, *args: Any) -> T:
        ...

    def sendblock(self, *args: Any) -> T:
        ...

    def superblockaverage(self, *args: Any) -> T:
        ...

    def versionreport(self, *args: Any) -> T:
        ...

    def writedata(self, *args: Any) -> T:
        ...

    def listmanifests(self, *args: Any) -> T:
        ...

    def getmpart(self, *args: Any) -> T:
        ...

    def sendscraperfilemanifest(self, *args: Any) -> T:
        ...

    def savescraperfilemanifest(self, *args: Any) -> T:
        ...

    def deletecscrapermanifest(self, *args: Any) -> T:
        ...

    def archivelog(self, *args: Any) -> T:
        ...

    def testnewsb(self, *args: Any) -> T:
        ...

    def convergencereport(self, *args: Any) -> T:
        ...

    def scraperreport(self, *args: Any) -> T:
        ...

    def addnode(self, *args: Any) -> T:
        ...

    def askforoutstandingblocks(self, *args: Any) -> T:
        ...

    def getblockchaininfo(self, *args: Any) -> T:
        ...

    def getnetworkinfo(self, *args: Any) -> T:
        ...

    def clearbanned(self, *args: Any) -> T:
        ...

    def currenttime(self, *args: Any) -> T:
        ...

    def getaddednodeinfo(self, *args: Any) -> T:
        ...

    def getnodeaddresses(self, *args: Any) -> T:
        ...

    def getbestblockhash(self, *args: Any) -> T:
        ...

    def getblock(self, *args: Any) -> T:
        ...

    def getblockbynumber(self, *args: Any) -> T:
        ...

    def getblockbymintime(self, *args: Any) -> T:
        ...

    def getblocksbatch(self, *args: Any) -> T:
        ...

    def getblockcount(self, *args: Any) -> T:
        ...

    def getblockhash(self, *args: Any) -> T:
        ...

    def getburnreport(self, *args: Any) -> T:
        ...

    def getcheckpoint(self, *args: Any) -> T:
        ...

    def getconnectioncount(self, *args: Any) -> T:
        ...

    def getdifficulty(self, *args: Any) -> T:
        ...

    def getinfo(self, *args: Any) -> T:
        ...

    def getnettotals(self, *args: Any) -> T:
        ...

    def getpeerinfo(self, *args: Any) -> T:
        ...

    def getrawmempool(self, *args: Any) -> T:
        ...

    def listbanned(self, *args: Any) -> T:
        ...

    def networktime(self, *args: Any) -> T:
        ...

    def ping(self, *args: Any) -> T:
        ...

    def setban(self, *args: Any) -> T:
        ...

    def showblock(self, *args: Any) -> T:
        ...

    def stop(self, *args: Any) -> T:
        ...

    def addpoll(self, *args: Any) -> T:
        ...

    def getpollresults(self, *args: Any) -> T:
        ...

    def getvotingclaim(self, *args: Any) -> T:
        ...

    def listpolls(self, *args: Any) -> T:
        ...

    def vote(self, *args: Any) -> T:
        ...

    def votebyid(self, *args: Any) -> T:
        ...

    def votedetails(self, *args: Any) -> T:
        ...
