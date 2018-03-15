import arcpy
import sys
import traceback
import logging
import time
import get_path
import os
from re import match, search
import path_links

formatter = ('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(filename=r"{}_Log_{}.csv".format(__name__.replace(".", "_"), time.strftime("%Y_%m_%d_%H_%M")),
                                 level=logging.DEBUG, format=formatter)

class overlap:
    def __init__(self, input_path=None, inputGDB=None, inputGDB2 = None, referenceGDB = None,
                 outputGDBname=None, outputpathfolder=None, outputfolder_name = None, outputGDB=None):
        self.input_path = input_path
        self.inputGDB = inputGDB
        self.inputGDB2 = inputGDB2
        self.referenceGDB = referenceGDB
        self.outputGDBName = outputGDBname
        self.outputpathfolder = outputpathfolder
        self.outputfolder_name = outputfolder_name
        self.outputGDB = outputGDB
        self.wildcard = ""

        arcpy.env.qualifiedFieldNames = False

    def create_folder(self):
        print("creating folder")
        logging.info("creating folder")
        try:
            if not os.path.exists(self.outputpathfolder):
                os.makedirs(self.outputpathfolder)

        except:
            tb = sys.exc_info()[2]
            tbinfo = traceback.format_tb(tb)[0]
            message = "Traceback info:\n" + tbinfo
            print(message)
            logging.warning(message)

    def create_gdb(self):
        print("Creating gdb")
        logging.info("Creating GDB named: {}".format(self.outputGDBName))
        try:
            arcpy.CreateFileGDB_management(out_folder_path=self.outputpathfolder, out_name=self.outputGDBName)
            print(arcpy.GetMessages(0))
            logging.info("created GDB, messages: {}".format(arcpy.GetMessages(0)))


        except arcpy.ExecuteError:
            msgs = arcpy.GetMessages(2)
            arcpy.AddError(msgs)
            print(msgs)
            logging.info(msgs)
        except:
            tb = sys.exc_info()[2]
            tbinfo = traceback.format_tb(tb)[0]
            pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
            msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
            arcpy.AddError(pymsg)
            arcpy.AddError(msgs)
            print(pymsg)
            print(msgs)
            logging.info(pymsg)
            logging.info(msgs)

    def import_shapefiles_to_gdb(self, wildcard=None):

        shplist = get_path.pathFinder.get_shapefile_path_wildcard(self.input_path, wildcard)

        print("\nI found {} files to import!!!".format(len(shplist)))

        try:
            for x in shplist:
                name = os.path.split(x)[1]
                output = os.path.join(self.outputGDB, name.strip(".shp"))
                print(output)
                logging.info("Importing: {}".format(name.strip(".shp")))
                if arcpy.Exists(output):
                    print("exists, passing over this fc")
                    logging.warning("{} exists, passing over this fc".format(name.strip(".shp")))
                else:
                    arcpy.FeatureClassToGeodatabase_conversion(x, self.outputGDB)
                    print(arcpy.GetMessages(0))
                    logging.info(arcpy.GetMessages(0))
        except:
            tb = sys.exc_info()[2]
            tbinfo = traceback.format_tb(tb)[0]
            pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
            msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
            arcpy.AddError(pymsg)
            arcpy.AddError(msgs)
            print(pymsg)
            print(msgs)
            logging.error(pymsg)

    def define_projection(self, wildcard, sr):
        logging.info("define projection")
        try:

            fc_list = get_path.pathFinder(env_0=self.inputGDB).get_file_path_with_wildcard_from_gdb(wildcard)

            for fc in fc_list:
                print("Defining projection for: {}, SR: {}".format(os.path.basename(fc), sr))
                arcpy.DefineProjection_management(fc, sr)
                logging.info(arcpy.GetMessages(0))

        except arcpy.ExecuteError:
            msgs = arcpy.GetMessages(2)
            arcpy.AddError(msgs)
            print(msgs)
            logging.info(msgs)
        except:
            tb = sys.exc_info()[2]
            tbinfo = traceback.format_tb(tb)[0]
            pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
            msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
            arcpy.AddError(pymsg)
            arcpy.AddError(msgs)
            print(pymsg)
            print(msgs)
            logging.info(pymsg)
            logging.info(msgs)


    def create_union_of_coverage_per_state(self):

        wildcard_fc = "coverage_map_{}_*".format(self.wildcard)
        print("wild card to find coverages is: {}".format(wildcard_fc))
        fc_list = get_path.pathFinder(env_0=self.inputGDB).get_file_path_with_wildcard_from_gdb(wildcard=wildcard_fc)

        if len(fc_list)==0:
            print("fc is empty, skipping")
        else:

            try:


                out_feature =  os.path.join(self.outputGDB, "coverage_map_union_{}".format(self.wildcard))
                if arcpy.Exists(out_feature):
                    print("the file exits, skipping!!!!!!!!")
                else:
                    print("creating union, for state: {}".format(self.wildcard))
                    arcpy.Union_analysis(fc_list, out_feature_class=out_feature,join_attributes="ONLY_FID")
                    logging.info(arcpy.GetMessages(0))
                    print(arcpy.GetMessages(0))

            except arcpy.ExecuteError:
                msgs = arcpy.GetMessages(2)
                arcpy.AddError(msgs)
                print(msgs)
            except:

                tb = sys.exc_info()[2]
                tbinfo = traceback.format_tb(tb)[0]
                pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
                msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
                arcpy.AddError(pymsg)
                arcpy.AddError(msgs)
                print(pymsg)
                print(msgs)
                logging.warning(msgs)



    def get_overlaps_by_state(self, path):

        def Get_fields_from_fc(input_fc):
            field_list = []
            for field in arcpy.ListFields(input_fc, "FID_*"):
                field_list.append(field.name)
            return field_list

        regex = r"(?:\W)?_(?P<state_fips>\d{1,2})_(?P<pid>\d{1,2})"

        wildcard_fc = "Coverage_map_union_{}".format(self.wildcard)
        fc_list = get_path.pathFinder(env_0=path).get_file_path_with_wildcard_from_gdb(wildcard=wildcard_fc)


        if len(fc_list) == 0:
            print("no coverage was found for {}, skipping".format(self.wildcard))
        else:

            field_list = Get_fields_from_fc(fc_list[0])

            try:


                while len(field_list) > 1:
                    fc = field_list.pop(0)
                    pid_dic = search(regex, fc).groupdict()
                    expression = '{} <>-1 AND ({})'.format(fc, ' OR '.join(['{} <>-1'.format(x) for x in field_list]))
                    print(expression)
                    temp_name = "overlap_{}_{}".format(pid_dic["state_fips"], pid_dic["pid"])
                    arcpy.Delete_management(temp_name)
                    print(temp_name)
                    arcpy.MakeFeatureLayer_management(in_features=fc_list[0],
                                                      out_layer=temp_name,
                                                      where_clause=expression)

                    arcpy.CopyFeatures_management(in_features=temp_name, out_feature_class=temp_name)
                    arcpy.Delete_management(temp_name)

            except arcpy.ExecuteError:
                msgs = arcpy.GetMessages(2)
                arcpy.AddError(msgs)
                print(msgs)
            except:

                tb = sys.exc_info()[2]
                tbinfo = traceback.format_tb(tb)[0]
                pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
                msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
                arcpy.AddError(pymsg)
                arcpy.AddError(msgs)
                print(pymsg)
                print(msgs)
                logging.warning(msgs)


    def merge_overlaps(self):

        wildcard_fc = "overlap_{}_*".format(self.wildcard)
        print(wildcard_fc)
        fc_list = get_path.pathFinder(env_0=self.inputGDB).get_file_path_with_wildcard_from_gdb(wildcard=wildcard_fc)
        if len(fc_list) == 0:
            print("fc list is empty, skipping this state: {}".format(self.wildcard))
        else:


            try:

                output = os.path.join(self.outputGDB, '_merged_overlaps_'+str(self.wildcard))

                if arcpy.Exists(output):
                    print("This file Exists, skipping!!!!!!!!!")
                else:
                    print("merging all of FCs for the state {}".format(self.wildcard))

                    arcpy.Merge_management(inputs=fc_list, output=output)
                    logging.info(arcpy.GetMessages(0))
                    print(arcpy.GetMessages(0))


            except arcpy.ExecuteError:
                msgs = arcpy.GetMessages(2)
                arcpy.AddError(msgs)
                print(msgs)
            except:

                tb = sys.exc_info()[2]
                tbinfo = traceback.format_tb(tb)[0]
                pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
                msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
                arcpy.AddError(pymsg)
                arcpy.AddError(msgs)
                print(pymsg)
                print(msgs)
                logging.warning(msgs)





    def erase_overlaps_from_coverages(self, pid_list_input=None):

        try:

            state_wildcard = self.wildcard

            if pid_list_input is None:

                pid_list = get_path.pathFinder.query_provider_by_FIPS(path_links.num_provider_per_state, str(int(state_wildcard)))
            else:
                pid_list = pid_list_input

            for pid in pid_list:

                fc_wildcard = "Coverage_map_{}_{}".format(self.wildcard, pid)
                print(fc_wildcard)
                fc_list = get_path.pathFinder(env_0=self.inputGDB).get_file_path_with_wildcard_from_gdb(fc_wildcard)

                erase_feature_list = get_path.pathFinder(env_0=self.inputGDB2).get_file_path_with_wildcard_from_gdb("_merged_overlaps_{}".format(self.wildcard))

                output = os.path.join(self.outputGDB, os.path.basename(fc_list[0])+"_minus_overlaps")

                if arcpy.Exists(output):
                    print("the file exits, skipping!!!!!!!!")
                else:
                    print("Erasing {} from coverage map {}".format(fc_list[0], erase_feature_list[0]))
                    arcpy.Erase_analysis(in_features=fc_list[0], erase_features=erase_feature_list[0],
                                         out_feature_class=output)
                    print(arcpy.GetMessages(0))
                    logging.info(arcpy.GetMessages(0))

        except arcpy.ExecuteError:
            msgs = arcpy.GetMessages(2)
            arcpy.AddError(msgs)
            print(msgs)
            logging.info(msgs)
        except:
            tb = sys.exc_info()[2]
            tbinfo = traceback.format_tb(tb)[0]
            pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
            msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
            arcpy.AddError(pymsg)
            arcpy.AddError(msgs)
            print(pymsg)
            print(msgs)
            logging.info(pymsg)
            logging.info(msgs)