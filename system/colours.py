# coding=utf-8
import string, sys

from colorama import Fore, Back, Style, init

init()

def colstrip(message, times=-1):
    if not message.strip(" ").strip("\n") == "":
        done = string.replace(message, "0", "")
        done = string.replace(done, "10", "")
        done = string.replace(done, "11", "")
        done = string.replace(done, "12", "")
        done = string.replace(done, "13", "")
        done = string.replace(done, "14", "")
        done = string.replace(done, "15", "")
        done = string.replace(done, "1", "")
        done = string.replace(done, "2", "")
        done = string.replace(done, "3", "")
        done = string.replace(done, "4", "")
        done = string.replace(done, "5", "")
        done = string.replace(done, "6", "")
        done = string.replace(done, "7", "")
        done = string.replace(done, "8", "")
        done = string.replace(done, "9", "")
        done = string.replace(done, "", "")
        return done
    return ""


def colprint(message):
    if not message.strip(" ").strip("\n") == "":
        message = " " + message
        done = string.replace(message, "0", Fore.WHITE + Style.BRIGHT)
        done = string.replace(done, "10", Fore.CYAN + Back.RESET + Style.DIM)
        done = string.replace(done, "11", Fore.CYAN + Back.RESET + Style.BRIGHT)
        done = string.replace(done, "12", Fore.BLUE + Back.RESET)
        done = string.replace(done, "13", Fore.MAGENTA + Back.RESET + Style.BRIGHT)
        done = string.replace(done, "14", Fore.WHITE + Back.RESET + Style.DIM)
        done = string.replace(done, "15", Fore.WHITE + Back.RESET + Style.NORMAL)
        done = string.replace(done, "1", Fore.BLACK + Back.WHITE + Style.NORMAL)
        done = string.replace(done, "2", Fore.BLUE + Back.RESET + Style.DIM)
        done = string.replace(done, "3", Fore.GREEN + Back.RESET + Style.DIM)
        done = string.replace(done, "4", Fore.RED + Back.RESET + Style.NORMAL)
        done = string.replace(done, "5", Fore.RED + Back.RESET + Style.DIM)
        done = string.replace(done, "6", Fore.MAGENTA + Back.RESET + Style.DIM)
        done = string.replace(done, "7", Fore.YELLOW + Back.RESET + Style.DIM)
        done = string.replace(done, "8", Fore.YELLOW + Back.RESET + Style.BRIGHT)
        done = string.replace(done, "9", Fore.GREEN + Back.RESET + Style.BRIGHT)
        done = string.replace(done, "", Fore.RESET + Back.RESET + Style.RESET_ALL)
        done = string.replace(done, "  ", " ")
        done = string.replace(done, "\t", "")
        done = done.lstrip()
        print(done + Fore.RESET + Back.RESET + Style.RESET_ALL)
