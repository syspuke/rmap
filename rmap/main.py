import nmap
from colorama import Fore
from rmap.utils import exec_cmd, exec_cmd_bash, hex_uuid, check_ping
import os
import xmltodict
import json
import logging
import sys
from libnmap.parser import NmapParser

class RMap:
    def __init__(self, host, nmap_all_ports, ffuf_wordlist, ffuf_outtype):
        self.host = host
        self.ffuf_wordlist = ffuf_wordlist
        self.ffuf_outtype = ffuf_outtype
        self.services = []
        self.nmap_all_ports = nmap_all_ports

        self.nmap()
        
    def nmap(self):
        exec_cmd("mkdir -p nmap")

        resultout = f"nmap_{self.host}"

        if self.nmap_all_ports:
            cmdnmap = f"nmap -sC -sV -p- -oA nmap/{resultout} {self.host}"
        else:
            cmdnmap = f"nmap -sC -sV -oA nmap/{resultout} {self.host}"

        print(Fore.RED + "[*]" + Fore.BLUE + f' Running...{cmdnmap}' + Fore.RESET)
        exec_cmd(cmdnmap)

        xml_path = f"nmap/{resultout}.xml"

        self.parse_nmap_file(xml_path)
        self.analyse_nmap()


    def ffuf_dir_enum(self, port):
        exec_cmd("mkdir -p ffuf")
        resultout = f"ffuf_{self.host}:{port}"
        cmdffuf = f"ffuf -w {self.ffuf_wordlist} -u http://{self.host}:{port}/FUZZ -o ffuf/{resultout}.{self.ffuf_outtype} -of {self.ffuf_outtype} -fc 302"
        print(Fore.RED + "[*]" + Fore.GREEN + f' [HTTP DETECTED] [{self.host}:{port}] Running...{cmdffuf}' + Fore.RESET)
        exec_cmd_bash(f"{cmdffuf} > ffuf/{resultout}.log")


    def nmap_smb_enum(self, port):
        exec_cmd("mkdir -p nmap")
        resultout = f"smb_{self.host}:{port}"
        cmdnmap = f"nmap --script=smb-enum-shares.nse,smb-enum-users.nse -p {port} -oA nmap/{resultout} {self.host}"

        print(Fore.RED + "[*]" + Fore.GREEN + f' [SMB DETECTED] [{self.host}:{port}] Running...{cmdnmap}' + Fore.RESET)
        exec_cmd(cmdnmap)


    def parse_nmap_file(self, path_xml):
        nmap_report = NmapParser.parse_fromfile(path_xml)

        services = []

        for host in nmap_report.hosts:
            if len(host.hostnames):
                tmp_host = host.hostnames.pop()
            else:
                tmp_host = host.address

            for serv in host.services:
                services.append(f"{serv.service}:{serv.port}")

        self.services = services

    def analyse_nmap(self):
        for service in self.services:
            service = service.split(":")
            if service[0] == "http":
                self.ffuf_dir_enum(service[1])
            elif service[0] == "microsoft-ds":
                self.nmap_smb_enum(service[1])
