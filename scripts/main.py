import asyncio
from bscscan import BscScan
from brownie.exceptions import RPCProcessError, VirtualMachineError
from module.contract import MyContract
from time import sleep
import time
from module.exceptions.local_chain_unavailable import LocalChainUnavailable
import csv
from typing import List
from execution_scheduler import store_csv
import os

YOUR_API_KEY = os.environ.get("BSCSCAN_API_KEY")


deployer_pancake = "0x0f9399fc81dac77908a2dde54bb87ee2d17a3373"
deployer_izumi = "0x3c2eB4b00a31286200de5CA26118c771f1a209C5"
deployer_izumi_2 = "0xaadcc13071fdf9c73cfbb8d97639ea68aa6fd1d2"
deployer_biswap = "0xc6aF770101dA859d680E0829380748CCcD8F7984"
deployer_pandora = "0x133a1BEc679F4C1e0e8bbCeAd382861c6f42d311"
deployer_beefy = "0xC362FA359031A081D21Cb9d57c29e055FecbcB06"


class ExecResCSV:
    project_name: str
    sc_addr: str
    call: str
    res_addr: str
    res_addr_type: str

    def __init__(self, project_name, sc_addr, call, res_addr, res_addr_type) -> None:
        self.project_name = project_name
        self.sc_addr = sc_addr
        self.call = call
        self.res_addr = res_addr
        self.res_addr_type = res_addr_type

    def __repr__(self) -> str:
        return f"{self.project_name},{self.sc_addr}, {self.call},{self.res_addr},{self.res_addr_type}"


class ProjectDetails:
    project_name: str
    sc_addr: str
    call: str
    res_addr: str
    res_addr_type: str


class ExecErrorCSV:
    project_name: str
    sc_addr: str
    call: str
    reason: str

    def __init__(self, project_name: str, sc_addr: str, call: str, reason: str) -> None:
        self.project_name = project_name
        self.sc_addr = sc_addr
        self.call = call
        self.reason = reason

    def __repr__(self) -> str:
        return f"{self.project_name}, {self.sc_addr}, {self.call}, {self.reason}"


def connect_brownie(disconnect=False):
    retries = 3
    if disconnect:
        network.disconnect()
        sleep(3)
    while retries:
        try:
            network.connect("bsc-fork")
            break
        except RPCProcessError as ex:
            print(ex)
        retries -= 1


def parse_csv(file_path, project_name_index, addr_index):
    project_name = project_name_index
    project_sc_addr = addr_index
    lst = []
    with open(file_path, newline="") as csvfile:
        csv_data = csv.reader(csvfile, delimiter=",", quotechar="|")
        for row in csv_data:
            name = row[project_name]
            addr = row[project_sc_addr]
            lst.append((name, addr))
    return lst


def get_fn_ret_addr(abi):
    """
    returns the function call in the case it returns address and has no input as parameter.
    used to potentiallly get roles
    """
    fns = []  # list of str fn calls returning addresses
    for obj in abi:
        if "outputs" in obj:
            if (
                len(obj["inputs"]) == 0
                and len(obj["outputs"]) == 1
                and obj["outputs"][0]["type"] == "address"
            ):
                fns.append(obj["name"] + "()")
    return fns


async def main_addresses():
    lst_results = []
    lst_errors = []

    connect_brownie()
    async with BscScan(YOUR_API_KEY) as bsc:
        for sc_addr in addrs:
            try:
                brownie_contract = await MyContract.from_explorer(bsc, sc_addr, True)
                if not brownie_contract.unverified:
                    contract_calls_def = get_fn_ret_addr(brownie_contract.abi)
                    await call_fns(
                        bsc,
                        brownie_contract.name,
                        brownie_contract,
                        lst_results,
                        lst_errors,
                        contract_calls_def,
                    )
            except LocalChainUnavailable as ex:
                print(ex)
                connect_brownie(True)
                contract_calls_def = get_fn_ret_addr(brownie_contract.abi)
                await call_fns(
                    bsc,
                    brownie_contract.name,
                    brownie_contract,
                    lst_results,
                    contract_calls_def,
                )
            except Exception as ex:
                err = ExecErrorCSV(brownie_contract.name, sc_addr, "", ex)
                lst_errors.append(err)
            if len(lst_results) > 0:
                store_csv("all_results_izumi.csv", lst_results)
                # reinitialize the results array
                lst_results = []
            if len(lst_errors) > 0:
                store_csv("all_errors_izumi.csv", lst_errors)
                # reinitialize the errors array
                lst_errors = []


async def main_single_project():
    lst_results = []
    lst_errors = []

    file_path = "./input/biswap/biswap.csv"
    res = []
    res.append(f"project_name, sc_addr,contract_name,verified")

    project_name_index = 0
    addr_index = 3
    connect_brownie()
    async with BscScan(YOUR_API_KEY) as bsc:
        project_details = parse_csv(file_path, project_name_index, addr_index)
        for project_name, sc_addr in project_details:
            try:
                brownie_contract = await MyContract.from_explorer(bsc, sc_addr, True)
                if not brownie_contract.unverified:
                    contract_calls_def = get_fn_ret_addr(brownie_contract.abi)
                    await call_fns(
                        bsc,
                        brownie_contract.name,
                        brownie_contract,
                        lst_results,
                        lst_errors,
                        contract_calls_def,
                    )
            except LocalChainUnavailable as ex:
                print(ex)
                connect_brownie(True)
                contract_calls_def = get_fn_ret_addr(brownie_contract.abi)
                await call_fns(
                    bsc, project_name, brownie_contract, lst_results, contract_calls_def
                )
            except Exception as ex:
                err = ExecErrorCSV(project_name, sc_addr, "", ex)
                lst_errors.append(err)
            if len(lst_results) > 0:
                store_csv("all_results_izumi.csv", lst_results)
                # reinitialize the results array
                lst_results = []
            if len(lst_errors) > 0:
                store_csv("all_errors_izumi.csv", lst_errors)
                # reinitialize the errors array
                lst_errors = []


async def main_top_100():
    """
    1. parse csv file DONE
    2. get contract abi from explorer DONE
    3. get list of all functions returning address DOne
    4. TODOCheck if uses Access Control from openzeppeling
    5. simulate call of function
    6. return execution
    """
    start_time = time.time()

    file_path = "./input/izumi/izumi.csv"
    res = []
    res.append(f"project_name, sc_addr,contract_name,verified")

    project_name_index = 0
    addr_index = 1
    lst_results = []
    lst_errors = []
    connect_brownie()
    batch = 100
    counter = 0
    async with BscScan(YOUR_API_KEY) as bsc:
        project_details = parse_csv(file_path, project_name_index, addr_index)
        for project_name, sc_addr in project_details:
            print(project_name, sc_addr)
            for project_from_list in projects:
                if (
                    is_similar_name(project_name, project_from_list)
                    and project_from_list != ""
                ):
                    print(project_name, sc_addr)
                    try:
                        brownie_contract = await MyContract.from_explorer(
                            bsc, sc_addr, True
                        )
                        if not brownie_contract.unverified:
                            contract_calls_def = get_fn_ret_addr(brownie_contract.abi)
                            await call_fns(
                                bsc,
                                project_name,
                                brownie_contract,
                                lst_results,
                                lst_errors,
                                contract_calls_def,
                            )
                    except LocalChainUnavailable as ex:
                        print(ex)
                        connect_brownie(True)
                        contract_calls_def = get_fn_ret_addr(brownie_contract.abi)
                        await call_fns(
                            bsc,
                            project_name,
                            brownie_contract,
                            lst_results,
                            contract_calls_def,
                        )
                    except Exception as ex:
                        err = ExecErrorCSV(project_name, sc_addr, "", ex)
                        lst_errors.append(err)
                    counter += 1
                    # if (counter % batch == 0):
                    # Store results every 100 records
                    break
                if len(lst_results) > 0:
                    store_csv("all_results.csv", lst_results)
                    # reinitialize the results array
                    lst_results = []
                if len(lst_errors) > 0:
                    store_csv("all_errors.csv", lst_errors)
                    # reinitialize the errors array
                    lst_errors = []
    print(f"--- Execution time: {(time.time() - start_time)/60} min")


def is_similar_name(name_from_list: str, name_from_file: str):
    name_from_list_lower = name_from_list.lower().split("-")[0]
    name_from_file_lower = name_from_file.lower()
    if name_from_list_lower in name_from_file_lower:
        print(f"{name_from_list_lower}  in  {name_from_file_lower}")
        return True


async def is_contract(bsc, addr):
    res = await bsc.get_proxy_code_at(addr)
    if res == "0x":
        return False
    else:
        return True


async def get_all_created_contracts(file_path, project_name_index, addr_index):
    '''
    - parse csv file with 'projectname_index;address_index'
    '''
    project_details = parse_csv(file_path, project_name_index, addr_index)
    projects = []
    async with BscScan(YOUR_API_KEY) as bsc:
        for project_name, deployer_addr in project_details:
            # res = await bsc.get_normal_txs_by_address(
            #     address=deployer_addr, startblock=0, endblock=99999999, sort="asc"
            # )

            # call the txlist action from etherscan
            # Returns the list of transactions performed by an address

            res = await bsc.get_normal_txs_by_address(
                address=deployer_addr, startblock=0, endblock=99999999, sort="asc"
            )
            project = ProjectContracts(project_name, deployer_addr)
            for item in res:
                # Api get the TX list
                new_addr = item["contractAddress"]
                if len(new_addr) > 0 and len(item["to"])==0:
                    project.add_contract(new_addr)
            projects.append(project)
            print(project)
            print()
    return projects


class ProjectContracts:
    project_name: str
    deployer_addr: str
    contracts: List[str]

    def __init__(self, project_name, deployer_addr) -> None:
        self.project_name = project_name
        self.deployer_addr = deployer_addr
        self.contracts = []

    def add_contract(self, contract):
        self.contracts.append(contract)

    def __repr__(self) -> str:
        res = ""
        for contract in self.contracts:
            res += f"{self.project_name},{self.deployer_addr},{contract}\n"
        return res


async def call_fns(
    bsc,
    project_name,
    contract: MyContract,
    contrac_res: list,
    contrac_err: list,
    list_calls,
):
    """
    dynamically executes the list of calls from the contract using brownie
    """
    for call in list_calls:
        call_to_do = f"contract.brownie_contract.{call}"
        call_res = ""
        try:
            call_res = eval(call_to_do)
        except VirtualMachineError as ex:
            print("Contract Owner: Brownie Virtual Machine exception")
            contrac_err.append(ExecErrorCSV(project_name, contract.addr, call, ex))
            print(ex)
        except ValueError as ex:
            print(ex)
            contrac_err.append(ExecErrorCSV(project_name, contract.addr, call, ex))
            pass
        except AttributeError as ex:
            contrac_err.append(ExecErrorCSV(project_name, contract.addr, call, ex))
            print(ex)
            pass
        if call_res and call_res != "0x0000000000000000000000000000000000000000":
            print(f"call res addr: {call_res}")
            # get owner contract

            is_cntr = await is_contract(bsc, call_res)
            if is_cntr:
                # check if the owner is SM
                addr_type = "SM"
            else:
                # check if the owner is EOA
                addr_type = "EOA"
            contrac_res.append(
                ExecResCSV(project_name, contract.addr, call, call_res, addr_type)
            )


if __name__ == "__main__":
    path = "./input/launchzone.csv"
    project_name_index = 0
    addr_index = 1
    res = asyncio.run(get_all_created_contracts(path, project_name_index, addr_index))
