import fnmatch
import os
import arcpy
import pandas as pd
import path_links

class pathFinder:


    def __init__(self, env_0=None, env_1=None, outPathFolder=None, outPathGDB = None):
        self.env_0 = env_0
        self.env_1 = env_1
        self.outPathFolder = outPathFolder
        self.outPathGDB = outPathGDB




    def get_path_for_all_feature_from_gdb(self, type ="Polygon"):
        gdbPath =[]
        for dirpath, dirnames, filenames in arcpy.da.Walk(self.env_0, datatype="FeatureClass", type=type):
            for filename in filenames:
                gdbPath.append(os.path.join(dirpath, filename))
        return gdbPath

    def get_file_path_with_wildcard_from_gdb(self, wildcard=None):
        arcpy.env.workspace = self.env_0
        fc = arcpy.ListFeatureClasses(wildcard)
        fc_list_path = []

        if fc is None:
            print("did not find fc, skipping")
            return fc_list_path
        else:

            for x in fc:
                fc_list_path.append(os.path.join(self.env_0, os.path.splitext(x)[0]))

            arcpy.ClearEnvironment("workspace")
            print("I found {} many file(s)".format(len(fc_list_path)))
            return fc_list_path



    @classmethod
    def get_shapefile_path_walk(cls, path):
        file_loc = []

        # use os.walk to find the root, directory, and files
        for root, dirs, files in os.walk(path):
            # create a loop by files
            for file in files:
                # for the files that endswith .shp, join the root and file
                if file.endswith(".shp"):
                    # create a local variable that we can assign the root and file path then loop it
                    path = os.path.join(root, file)
                    # append the path in our file_loc list
                    file_loc.append(path)

        return list(file_loc)


    @classmethod
    def get_shapefile_path_wildcard(cls, path, wildcard):
        file_loc = []

        # use os.walk to find the root, directory, and files
        for root, dirs, files in os.walk(path):
            # create a loop by files
            for file in fnmatch.filter(files, wildcard+".shp"):
                # for the files that endswith .shp, join the root and file
                file_loc.append(os.path.join(root, file))

        if list(file_loc) == 'NoneType':
            raise Warning("Did not find path, check your wild card")

        else:
            return list(file_loc)

    @classmethod
    # create a list of fips from the table.
    def make_fips_list(cls):
        import pandas as pd
        Fips_table_path = path_links.fips_table
        data = pd.read_csv(Fips_table_path, sep='|')
        data["STATE"] = data["STATE"].astype(str)
        data['STATE'] = data["STATE"].apply(lambda x: x.zfill(2))
        return data.STATE.tolist()

    @classmethod
    def query_provider_by_FIPS(cls, path, fips):
        import pandas as pd
        df = pd.read_csv(path)
        fips_query = df.query("stateFIPS ==" + str(fips))
        fips_query = fips_query.dropna(axis=1, how="any")
        return list(fips_query.applymap(int).values.flatten()[1:])



