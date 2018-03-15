import Overlapchecker
import sys
import time
import get_path
from arcpy import Exists
import os
import path_links

state_list = []

while True:

    input_list = str(input(
        "which state fips do you want to add, please zero pad and one state at a time\n\nor\n\ntype '*' to run for all states\n\nor\n\ntype q to exit:  "))

    if input_list != "q" and input_list != "*":

        state_list.append(input_list)

        confirm_response = str(input("do you want to add another file state? n/y:  "))

        if confirm_response.lower() == "y":
            continue
        if confirm_response.lower() == "n":
            break

        if confirm_response.lower() != "y" or confirm_response.lower() != "n":
            print("i am sorry, not a valid statement!!!!")


    elif input_list == "*":
        state_list = get_path.pathFinder.make_fips_list()
        break

    elif input_list == "q":
        print("bye")
        time.sleep(0.5)
        sys.exit()

print(state_list)
for state in state_list:

    print("working on state: {}".format(state))
    overlaps = Overlapchecker.overlap()
    overlaps.inputGDB = path_links.provider_coverages
    overlaps.outputpathfolder = path_links.input_base_folder
    overlaps.outputGDBName = "_01_Union_and_coverages"
    overlaps.outputGDB = os.path.join(overlaps.outputpathfolder, overlaps.outputGDBName+".gdb")
    overlaps.wildcard = state
    if Exists(overlaps.outputGDB):
        overlaps.create_union_of_coverage_per_state()
        overlaps.get_overlaps_by_state(path=overlaps.outputGDB)
    else:
        overlaps.create_gdb()
        overlaps.create_union_of_coverage_per_state()
        overlaps.get_overlaps_by_state(path=overlaps.outputGDB)

    # merging overlaps
    merge = Overlapchecker.overlap()
    merge.inputGDB = overlaps.outputGDB
    merge.outputpathfolder = path_links.input_base_folder
    merge.outputGDBName = "_02_merged_overlaps"
    merge.outputGDB = os.path.join(merge.outputpathfolder, merge.outputGDBName + ".gdb")
    merge.wildcard = str(state)

    if Exists(merge.outputGDB):
        merge.merge_overlaps()
    else:
        merge.create_gdb()
        merge.merge_overlaps()


    #erase overlaps

    erase_overlaps = Overlapchecker.overlap()
    erase_overlaps.inputGDB = path_links.provider_coverages
    erase_overlaps.inputGDB2 = merge.outputGDB

    erase_overlaps.outputpathfolder = path_links.output_base_folder
    erase_overlaps.outputGDBName = "_03_Erase_coverages"
    erase_overlaps.outputGDB = os.path.join(erase_overlaps.outputpathfolder, erase_overlaps.outputGDBName + ".gdb")
    erase_overlaps.wildcard = str(state)
    if Exists(erase_overlaps.outputGDB):
        erase_overlaps.erase_overlaps_from_coverages()
    else:
        erase_overlaps.create_gdb()
        erase_overlaps.erase_overlaps_from_coverages(pid_list_input=["60", "74"])