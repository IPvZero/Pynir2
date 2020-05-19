import os
import subprocess
from colorama import Fore, Style
from nornir import InitNornir
from nornir_scrapli.tasks import send_command, send_interactive
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.functions.text import print_result, print_title
from nornir.plugins.tasks.networking import netmiko_send_config
from nornir.plugins.tasks.data import load_yaml
from nornir.plugins.tasks.text import template_file
from pyfiglet import Figlet

nr = InitNornir(config_file="config.yaml")
clear_command = "clear"
os.system(clear_command)
custom_fig = Figlet(font='isometric3')
print(custom_fig.renderText('pyNIR'))



def rollback_golden(task):
    cmds = [
            ("configure replace flash:golden-commit",
            "Enter Y if you are sure you want to proceed. ? [no]", False),
            ("Y\n",
            f"{task.host}#", False)
]
    task.run(task=send_interactive,name="Rolling Back...",interact_events=cmds)

def load_vars(task):
    data = task.run(task=load_yaml,file=f'./host_vars/{task.host}.yaml')
    task.host["facts"] = data.result

def load_base(task):
    b = task.run(task=template_file,name="Buildling Base Configuration",template="base.j2", path="./templates")
    task.host["base_config"] = b.result
    base_output = task.host["base_config"]
    base_send = base_output.splitlines()
    task.run(task=netmiko_send_config, name="Pushing Base Commands", config_commands=base_send)

def load_isis(task):
    i = task.run(task=template_file,name="Building IS-IS Configuration",template="isis.j2", path="./templates")
    task.host["isis_config"] = i.result
    isis_output = task.host["isis_config"]
    isis_send = isis_output.splitlines()
    task.run(task=netmiko_send_config, name="Pushing IS-IS Commands", config_commands=isis_send)

def load_ether(task):
    e = task.run(task=template_file,name="Building Etherchannel Configuration",template="etherchannel.j2", path="./templates")
    task.host["ether_config"] = e.result
    ether_output = task.host["ether_config"]
    ether_send = ether_output.splitlines()
    task.run(task=netmiko_send_config, name="Pushing Etherchannel Commands", config_commands=ether_send)


def load_trunking(task):
    t = task.run(task=template_file,name="Building Trunk Configuration",template="trunking.j2", path="./templates")
    task.host["trunk_config"] = t.result
    trunk_output = task.host["trunk_config"]
    trunk_send = trunk_output.splitlines()
    task.run(task=netmiko_send_config, name="Pushing Trunk Commands", config_commands=trunk_send)


def load_vlan(task):
    v = task.run(task=template_file,name="Building VLAN Configuration",template="vlan.j2", path="./templates")
    task.host["vlan_config"] = v.result
    vlan_output = task.host["vlan_config"]
    vlan_send = vlan_output.splitlines()
    task.run(task=netmiko_send_config, name="Pushing VLAN Commands", config_commands=vlan_send)



current = "pyats learn config vlan --testbed-file testbed.yaml --output current-config"
os.system(current)
command = subprocess.run(["pyats", "diff", "golden-config/", "current-config", "--output", "configs-diff"], stdout=subprocess.PIPE)
stringer = str(command)
if "Diff can be found" in stringer:
    os.system(clear_command)
    print(Fore.CYAN + "#" * 70)
    print(Fore.RED + "ALERT: " + Style.RESET_ALL + "CURRENT CONFIGURATIONS ARE NOT IN SYNC WITH GOLDEN CONFIGS!")
    print(Fore.CYAN + "#" * 70)
    print("\n")
    answer = input(Fore.YELLOW +
            "Would you like to reverse the current configuration back to their golden state? " + Style.RESET_ALL + "<y/n>: "
)
    if answer == "y":
        def main() -> None:
            clean_up = "rm -r configs-diff current-config"
            os.system(clean_up)
            os.system(clear_command)
            nr = InitNornir(config_file="config.yaml")
            wipe_targets = nr.filter(all="yes")
            wipe_results = wipe_targets.run(task=rollback_golden)
            yaml_targets = nr.filter(all="yes")
            yaml_results = yaml_targets.run(task=load_vars)
            base_targets = nr.filter(all="yes")
            base_results = base_targets.run(task=load_base)
            isis_targets = nr.filter(routing="yes")
            isis_results = isis_targets.run(task=load_isis)
            ether_targets = nr.filter(etherchannel="yes")
            ether_results = ether_targets.run(task=load_ether)
            trunk_targets = nr.filter(trunking="yes")
            trunk_results = trunk_targets.run(task=load_trunking)
            vlan_targets = nr.filter(vlan="yes")
            vlan_results = vlan_targets.run(task=load_vlan)
            print_result(wipe_results)
            print_result(yaml_results)
            print_result(base_results)
            print_result(isis_results)
            print_result(ether_results)
            print_result(trunk_results)
            print_result(vlan_results)

        if __name__ == '__main__':
                main()

else:
    clean_up = "rm -r ospfdiff ospf-current"
    os.system(clean_up)
    os.system(clear_command)
    print("*" * 75)
    print(Fore.GREEN + "Good news! Current configurations are matching their golden state!" + Style.RESET_ALL)
    print("*" * 75)
