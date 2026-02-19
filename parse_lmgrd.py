import os, sys, string, re, csv
from datetime import datetime, timedelta, time
from typing import List
from collections import defaultdict



# ---------------------------------------------------------------------------------------



class Check():
    """
    Check class

    contains content of IN: and OUT: lines
        for example original timestamp, vendor, user ...
    additionally further attributes are stored for later processing
        for example date_time, duration ...

    """ 
    def __init__(self, t, vend, in_out, mscone, user, feat, lic, dt):
        # timestamp, vendor, in_out, mscone, user
        self.timestamp = t
        self.vendor = vend
        self.in_out = in_out
        self.mscone = mscone
        self.user = user
        # feature, lic, date_time, duration, total_lic
        self.feature = feat
        self.lic = lic
        self.date_time = dt
        self.duration = 0.0
        self.total_lic = 0
        # sum_list
        self.sum_list = []
        
    def set_timestamp(self,value): self.timestamp = value
    def set_total_lic(self,value): self.total_lic = value
    def set_sum_list(self,values): self.sum_list = values

    def get_sum_list(self): return self.sum_list

    def get_debug_printout(self):
        return self.timestamp, self.vendor, self.in_out, self.mscone, self.user, \
            self.feature, self.lic, self.date_time, self.duration, self.total_lic, \
            len(self.sum_list)



class Tokens():
    """
    Tokens class

    class as main storage of license information as:
    - all checks marked with IN: and OUT:
    - separate start dates as storage of deamon start times
      
    """
    def __init__(self, lmgrd_file):
        """
        init
        
        initialize class and define attributes and methods
        """
        # lmgrd log file
        self.lmgrd_file = lmgrd_file
        # saved input date
        self.check_list = []
        self.start_dates = []
        # post data
        self.total_duration = 0.0
        self.total_tok_min = 0.0
        self.all_features = []
        self.token_minutes = {}
        self.feature_minutes = {}
        self.per_day_tok_min = {}
        self.queued = []
        # log information
        self.log = []
    


# =======================================================================================
# INPUT



    def read_lmgrd_file(self):
        """
        function read_lmgrd_file
        
        read log file and save IN: and OUT: data in object
        save that object in a list
        """
        self.log.append("... reading: " + self.lmgrd_file)
        print("... reading", self.lmgrd_file)
        # set now as default start_date 
        _, current_date, start_time = self.extract_date_time("")
        save_time = "00:00:00"
        current_lic = 0
        out_list = []
        # read log file
        file_in = open(self.lmgrd_file,'r')
        line_list = file_in.readlines()
        file_in.close()
        # loop through lines
        for line in line_list:
            line = line.strip()
            splitted = line.split()
            # save any checks
            try:
                if splitted[2] == "IN:" or splitted[2] == "OUT:":
                    t = splitted[0]                   # '16:30:39'
                    vend = splitted[1].strip('())')   # '(MSC)'
                    in_out = splitted[2]              # 'IN:' oder 'OUT:'
                    mscone = splitted[3]              # '"MSCONE"'
                    user = splitted[4]                # 'paul@machine_01'
                    feat = splitted[5].strip('[]')    # '[MSCONE:Mentat]'
                    lic_raw = splitted[6]             # '(5', 'licenses)'
                    lic = int(lic_raw.strip('()[]'))
                    # set date time from start deamon - check for day count
                    day_count = self.get_day_count(t, save_time)
                    if day_count > 0:
                        current_date = self.add_one_day(current_date)
                        # print ("... day counted to: ", current_date)
                    dt = current_date + " " + t
                    # store previous time for next midnight check
                    save_time = t
                    # calculate current licenses
                    if in_out == "OUT:":
                        current_lic = current_lic + lic
                    if in_out == "IN:":
                        current_lic = current_lic - lic
                    # update checked-out license list
                    if in_out == "OUT:":
                        out_list.append( (feat, lic) )
                    if in_out == "IN:":
                        try:
                            out_list.remove( (feat, lic) )
                        except:
                            print ("not able to remove  ",feat," - ", lic, "from out_list ...")
                    # put values in object and append object to Tokens
                    a = Check(t, vend, in_out, mscone, user, feat, lic, dt)
                    a.set_total_lic(current_lic)
                    a.set_sum_list(out_list)
                    self.check_list.append(a)
                    # fill all-features
                    if (feat, int(lic)) not in self.all_features:
                        self.all_features.append((feat, int(lic)))
            except:
                pass
            # save any start times
            try:
                if "Start-Date:" in line:
                    # store start date in object
                    current_dt,current_date,current_time = self.extract_date_time(line)
                    self.start_dates.append( [current_dt, current_date, current_time] )
                    print("deamon start date: ", current_date)
            except:
                pass
            # queued events
            # get last check-out object and replace checkout-time with queue-time
            try:
                if splitted[2] == "QUEUED:":
                    queued_check = Check(t, vend, in_out, mscone, user, feat, lic, dt)
                    queued_check.set_total_lic(current_lic)
                    queued_check.set_sum_list(out_list.copy())  
                    self.queued.append(queued_check)
            except:
                pass
        # return variables
        num_checks = len(self.check_list)
        num_starts = len(self.start_dates)
        self.log.append(str(len(line_list))+","+str(num_checks)+","+str(num_starts))
        print("lines, checks, queued,starts: ", \
              str(len(line_list)), str(num_checks), str(len(self.queued)), str(num_starts))
        return num_checks, num_starts








    def process_data(self):
        """
        function process_data
        
        use list of objects to read and process several statistics
        """
        # variables
        flags = [0] * len(self.check_list)  
        
        
        # loop over objects
        for i, obj in enumerate(self.check_list):
            # jump over:
            #     if flagged already to 1
            #     or not checked out
            if flags[i] == 1 or obj.in_out != 'OUT:':  
                continue
            # check out time and attributes for comparison (user, feature, lic)
            out_dt = obj.date_time
            
            
            # find IN: that fits to OUT: attributes (user, feature, lic)
            for j, obj_in in enumerate(self.check_list[i+1:], i+1):
                # compare attributes, found a pairing, a claim
                if (flags[j] == 0 and obj_in.in_out == 'IN:' and
                    obj_in.user == obj.user and obj_in.feature == obj.feature and obj_in.lic == obj.lic):
                    # check-in time and duration of claim
                    in_dt = obj_in.date_time
                    duration_sec, duration_min, duration_h = self.get_duration(out_dt, in_dt)
                    obj.duration = duration_sec

                    
                    # flag IN: and OUT: as processed for time and lic tracking
                    flags[i] = 1  
                    flags[j] = 1  
                    break
                # if-block
            # loop through objects
        
        # return value
        return 0



# =======================================================================================
# POSTPROCESSING


        
    def post_data(self):
        # variables
        day = 1
        prev_date = None
        minutes = 0.0
        t_minutes = 0.0
        d_tok_min = {}
        # loop - token usage filled into post-dictionaries
        for i, obj in enumerate(self.check_list):
            if obj.in_out == "OUT:" and obj.duration > 0.0:
                # get minutes and token-minutes
                minutes = float(obj.duration) / 60.0
                t_minutes = float(obj.lic) * minutes
                # total sum of minutes and token minutes
                self.total_duration = self.total_duration + minutes
                self.total_tok_min = self.total_tok_min + t_minutes
                # get day information
                dt = datetime.strptime(obj.date_time, "%Y-%m-%d %H:%M:%S")
                curr_date = dt.date()
                # add to intra-day-token-minutes
                if (obj.feature, obj.lic) in d_tok_min:
                    d_tok_min[(obj.feature, obj.lic)] += t_minutes
                else:
                    d_tok_min[(obj.feature, obj.lic)] = t_minutes                
                # set initial date 
                if prev_date is None:
                    prev_date = curr_date
                # day changed
                # store collected license information for that day
                elif curr_date != prev_date:
                    # save per-day data in post-dictionary
                    self.per_day_tok_min[prev_date] = d_tok_min
                    d_tok_min = {}
                    # reset loop variables
                    day += 1
                    prev_date = curr_date
                    print ("counted: ", curr_date, prev_date, i)
                # add on feature-minutes
                if obj.feature in self.feature_minutes:
                    self.feature_minutes[obj.feature] += minutes
                else:
                    self.feature_minutes[obj.feature] = minutes
                # add on token-minutes
                if (obj.feature, obj.lic) in self.token_minutes:
                    self.token_minutes[(obj.feature, obj.lic)] += t_minutes
                else:
                    self.token_minutes[(obj.feature, obj.lic)] = t_minutes
            # if block
        # loop
        # return value
        return 0



# =======================================================================================
# OUTPUT



    def csv_lic_time_line(self):
        """
        get_lic_time_line
        
        license usage over time → writes CSV file for Excel timeline chart
        Format: "2026-02-13 14:30:25";5
        """
        filename = "license_timeline.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(['time', 'lic'])            
            for obj in self.check_list:
                if hasattr(obj, 'total_lic') and obj.total_lic is not None:
                    writer.writerow([obj.date_time, obj.total_lic])
                


    def csv_feature_and_token_minutes(self):
        """
        csv_feature_and_token_minutes

        get feature and token minutes total and per day in csv file
        
        """
        # variables
        feature_min_perc = []
        feat_tok_min_perc = []
        csv_01 = "feature_and_token_minutes.csv"
        # pct prep
        for f, m in self.feature_minutes.items():
            pct = (m / self.total_duration) * 100.0
            feature_min_perc.append([f,m,pct])
        # feature list with tok-min and pct
        for f, m in self.token_minutes.items():
            pct = (m / self.total_tok_min) * 100.0
            feat_tok_min_perc.append([f,m,pct])
        # write csv file - 01
        with open(csv_01, 'w', encoding='utf-8') as f:
            # feature minutes
            f.write("feature;feat_min;percentage\n")  
            for data in feature_min_perc:
                wert_min = f"{data[1]:.2f}".replace(".", ",")
                wert_pct = f"{data[2]:.1f}%".replace(".", ",")
                f.write(f"{data[0]};{wert_min};{wert_pct}\n")
            # separator
            f.write(" \n")
            # feature token-minutes
            f.write("feature;token_min;percentage\n")  
            for data in feat_tok_min_perc:
                wert_min = f"{data[1]:.2f}".replace(".", ",")
                wert_pct = f"{data[2]:.1f}%".replace(".", ",")
                f.write(f"{data[0]};{wert_min};{wert_pct}\n")
        # return value
        return 0



    def csv_daily_token_minutes(self):
        """
        csv_daily_token_minutes

        get feature and token minutes total and per day in csv file
        
        """
        # variables
        csv_01 = "daily_token_minutes_list.csv"
        csv_02 = "daily_token_minutes_stacked.csv"
        header = ""
        line_01 = ""
        line_02 = ""
        t_values = []
        sum_tok_min = 0.0
        # write csv file - 01
        with open(csv_01, 'w', encoding='utf-8') as f:
            for k,v in self.per_day_tok_min.items():
                line_01 = ""
                line_02 = ""
                for k1,v1 in v.items():
                    line_01 = line_01 + str(k1) + ";" 
                    v1_str = f"{v1:.1f}".replace(".", ",")
                    line_02 = line_02 + v1_str  + ";"
                    sum_tok_min = sum_tok_min + v1
                sum_str = f"{sum_tok_min:.1f}".replace(".", ",")
                line_01 = str(k) + ";" + line_01 + "\n"
                line_02 = str(sum_str) + ";" + line_02 + "\n"
                f.write(line_01) 
                f.write(line_02)
                sum_tok_min = 0.0
        # write csv file - 02
        with open(csv_02, 'w', encoding='utf-8') as f:
            header = "date;" + ";".join(map(str, self.all_features))
            f.write(header + "\n")
            t_values = [0.0] * len(self.all_features)
            for d,d_data in self.per_day_tok_min.items():
                # line_01 = str(d) + ";"
                for feat,value in d_data.items():
                    t_values[self.all_features.index(feat)] = value
                line_01 = str(d) + ";" + ";".join(f"{v:.2f}".replace(".", ",") for v in t_values)
                f.write(line_01 + "\n")







    def csv_queued_tables(self):
        """
        csv_queued_tables

        get information about queued status
        
        """
        # variables
        csv = "queued_events.csv"
        feat_dict = {}
        start_status = []
        end_status = []
        lines = []
        # get start and end time
        obj = self.check_list[0]
        start_status = [obj.date_time, obj.total_lic]
        obj= self.check_list[len(self.check_list)-1]
        end_status = [obj.date_time, obj.total_lic]
        # loop over all queued
        for i, obj in enumerate(self.queued):
            feat_dict = {}
            for feat, count in obj.get_sum_list():
                if feat in feat_dict:
                    feat_dict[feat] += count
                else:
                    feat_dict[feat] = count
            feat_list=list(feat_dict.items())
            lines.append("queued_"+str(i+1)+";"+str(obj.date_time)+";"+str(obj.total_lic))
            lines.extend(["",""])
            for items in feat_list:
                lines[(i*3)+1] = lines[(i*3)+1] + str(items[0]) + ";"
                lines[(i*3)+2] = lines[(i*3)+2] + str(items[1]) + ";"
        # csv
        with open(csv, 'w', encoding='utf-8') as f:
            f.write(start_status[0]+";"+"start"+";"+str(start_status[1])+"\n")
            for i, obj in enumerate(self.queued):
                f.write(str(obj.date_time) + ";" + "queued_"+str(i+1)+";"+str(obj.total_lic)+"\n")
            f.write(str(end_status[0])+";"+"end"+";"+str(end_status[1])+"\n")
            f.write("; ; ;\n")
            for l in lines:
                f.write(l + "\n")
        
            










# =======================================================================================
# OTHER



    def timestamp_to_seconds(self, ts):
        dt = datetime.strptime(ts, '%H:%M:%S')
        return dt.hour * 3600 + dt.minute * 60 + dt.second

    def extract_date_time(self, line):
        # 14:26:16 (MSC) (@MSC-SLOG@) Start-Date: Sun Sep 21 2025 14:26:16 India Standard 
        # 2025-09-21 14:26:16
        if len(line) > 0:
            pattern = r"(\w{3}\s\w{3}\s\d{1,2}\s\d{4}\s\d{2}:\d{2}:\d{2})"
            match = re.search(pattern, line)
            if match: 
                dt_str = datetime.strptime(match.group(1), "%a %b %d %Y %H:%M:%S")
                date_str = dt_str.strftime("%Y-%m-%d")      
                time_str = dt_str.strftime("%H:%M:%S")     
        # set to current date with time 00:00:01
        if len(line) == 0:
            today = datetime.combine(datetime.now().date(), time(0, 0, 1))
            dt_str = today.strftime("%Y-%m-%d %H:%M:%S")
            date_str = today.strftime("%Y-%m-%d")
            time_str = today.strftime("%H:%M:%S")
        # three return variables, date_time, date, 
        return dt_str, date_str, time_str

    def get_duration(self, out_dt, in_dt):
        # bring into format
        start = datetime.strptime(out_dt, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(in_dt, "%Y-%m-%d %H:%M:%S")  
        # difference
        delta = end - start
        # units: s, min, h
        total_sec = int(delta.total_seconds())
        min = total_sec // 60
        h = total_sec // 3600
        # three variables as return
        return total_sec, min, h    
    
    def get_day_count(self, t, save_time):
        day_count = 0
        last_time = datetime.strptime(save_time, "%H:%M:%S")
        curr_time = datetime.strptime(t, "%H:%M:%S")
        time_diff = (curr_time - last_time).total_seconds()
        if time_diff < 0:
            day_count = 1
        return day_count

    def add_one_day(self,date_str):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        new_date_obj = date_obj + timedelta(days=1)
        new_date_str = new_date_obj.strftime("%Y-%m-%d")
        return new_date_str

    def get_debug_printout(self, size):
        if size == "SMALL":
            num = 10
        if size == "MEDIUM":
            num = 50
        if size == "LARGE":
            num = -1
        for i, entry in enumerate(self.start_dates):
            if num == -1 or i <= num:
                print (entry)
        for i, obj in enumerate(self.check_list):
            if num == -1 or i <= num:
                print (obj.get_debug_printout())



# =======================================================================================



def main():
    """
    main function


    """
    # argument handling
    print (sys.version)
    print(os.getcwd())
    print(sys.argv)
    try:
        log_file = sys.argv[1]
    except:
        log_file = "lmgrd_45_r001.log"
    # (0) instance of object
    t = Tokens(log_file)
    # (1) read and process data
    t.read_lmgrd_file()
    t.process_data()
    # (2) post processing
    t.post_data()
    # (3) output to csv
    t.csv_lic_time_line()
    t.csv_feature_and_token_minutes()
    t.csv_daily_token_minutes()
    t.csv_queued_tables()
    


# =======================================================================================
if __name__ == "__main__":
    main()   
   
# =======================================================================================    
# 
# 13:23:41 (MSC) IN: "MSCONE" msiwani@SPA06CMW000201  [MSCONE:MSC_Apex_Modeler] (15 licenses)
# 13:37:20 (MSC) OUT: "MSCONE" jfedewa@spa06cdw000073  [MSCONE:PA_ANALYSIS_MANAGER] (2 licenses)
# 13:37:20 (MSC) Acquired 2 licenses for Group MSCONE (MSC Analysis Manager)
# 13:37:21 (MSC) IN: "MSCONE" jfedewa@spa06cdw000073  [MSCONE:PA_ANALYSIS_MANAGER] (2 licenses)
# 13:37:21 (MSC) Returned 2 licenses for Group MSCONE (MSC Analysis Manager)
# 13:37:50 (MSC) OUT: "MSCONE" jfedewa@spa06cdl000002  [MSCONE:NASTRAN] (13 licenses)
# 13:37:50 (MSC) Acquired 13 licenses for Group MSCONE (MSC Nastran)    