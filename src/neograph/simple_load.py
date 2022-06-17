####################################################
# Load formatted data from CSV into Neo4J using OGM
# (neomodel). Individiuals models defined in:
# models.simple_graph
####################################################

from models.simple_graph import *
from tqdm import tqdm


class SimpleGraph:
    def run_import(self, csv_path):
        try:
            # Count number of lines for use in TQDM
            num_lines = 0
            with open(csv_path) as mimic_data:
                for line in mimic_data:
                    num_lines += 1

            # Reopen file for processing
            with open(csv_path) as mimic_data:
                header = []

                i = 0
                for line in tqdm(mimic_data, total=num_lines, desc="Loading data..."):
                    i += 1
                    # Strip newlines, remote quotes from strings, and split CSV
                    entry = line.strip().replace('"', "").split(",")
                    
                    # Process header and create diagnostic code relationships
                    # Diagnostic codes in ICD9
                    if i == 1:
                        header = entry
                        
                        # For each diagnosis, add to Neo4J and create hierarchy 
                        for z in range(7, len(header)):
                            icd9 = header[z].replace(".", "")

                            base_length = 3
                            # For ICD9, if it start with E, base code is length 4 instead of 3 
                            if icd9.startswith("E"):
                                base_length = 4
                            
                            # This actually creates the hierarchy as a directional relationship
                            last = None
                            for j in range(base_length, len(icd9)):
                                cur_icd = icd9[0:j]
                                cur_dx = Diagnosis.get_or_create(
                                    {
                                        "icd": cur_icd
                                    }
                                )
                                if last is not None:
                                    cur_dx[0].parent_dx.connect(last[0])
                                last = cur_dx
                                
                        continue # Since header, now move on to read/process data
                    
                    # When a data row, get variables and add to Neo4J via neomodel
                    visit_id = entry[0]
                    sex = entry[1]
                    care_site = entry[2]
                    race = entry[3]
                    age = entry[4]

                    sex_node = Sex.get_or_create(
                        {
                            "label": sex.lower()
                        }
                    )
                    care_site_node = CareSite.get_or_create(
                        {
                            "site_id": str(care_site).lower()
                        }
                    )
                    race_node = Race.get_or_create(
                        {
                            "label": race.lower()
                        }
                    )
                    age_node = Age.get_or_create(
                        {
                            "label": age.lower()
                        }
                    )
                    visit_node = Visit.create_or_update(
                        {
                            "visit_id": str(visit_id).lower()
                        }
                    )
                    
                    # Connect each of the data elements to the visit node
                    visit_node[0].sex.connect(sex_node[0])
                    visit_node[0].care_site.connect(care_site_node[0])
                    visit_node[0].race.connect(race_node[0])
                    visit_node[0].age.connect(age_node[0])

                    # Add diagnosis nodes and connect to the visit
                    for z in range(7, len(header)):
                        if entry[z] == "1" or entry[z] == 1:
                            icd9 = header[z].replace(".", "")
                            cur_dx = Diagnosis.get_or_create(
                                        {
                                            "icd": icd9
                                        }
                                    )
                            visit_node[0].dx.connect(cur_dx[0])

        except Exception as ex:
            print(ex)
