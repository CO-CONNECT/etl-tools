from coconnect.tools.bclink_helpers import BCLinkHelpers
from .local import LocalDataCollection
import io
import pandas as pd
import time

class BCLinkDataCollection(LocalDataCollection):
    def __init__(self,bclink_settings,**kwargs):
            
        self.logger.info('setup bclink collection')
        self.bclink_helpers = BCLinkHelpers(**bclink_settings)
        
        super().__init__(**kwargs)
        self.job_ids = []

    def finalise(self):
        self.logger.info("finalising, waiting for jobs to finish")
        self.logger.info(f"job_ids to wait for: {self.job_ids}")

        #print (self.get_output_folder())

        running_jobs = self.job_ids
        while True:
            running_jobs = [j for j in running_jobs if not self.bclink_helpers.check_logs(j)]
            if len(running_jobs)==0:
                break
            self.logger.info(f"Waiting for {running_jobs} to finish")
            time.sleep(5)
         
        self.logger.info(f"done!")

    def write(self,*args,**kwargs):
        f_out = super().write(*args,**kwargs)
        destination_table = args[0]
        job_id = self.bclink_helpers.load_table(f_out,destination_table)
        if job_id:
            self.job_ids.append(job_id)
        
    def load_indexing(self):
        indexer = self.bclink_helpers.get_indicies()
        if indexer:
            self.logger.info(f'retrieved {indexer}')
        return indexer

    def load_global_ids(self):
        data = self.bclink_helpers.get_global_ids()
        if not data:
            return
        if len(data.splitlines()) == 0:
            return

        sep = self.get_separator()
        data = io.StringIO(data)
        df_ids = pd.read_csv(data,
                             sep=sep).set_index('TARGET_SUBJECT')['SOURCE_SUBJECT']
        return df_ids.to_dict()