# pyWoSRedemptionTool
This Python-based tool is designed for redeeming Whiteout Survival Gift Codes. Initially created to manage the ZEN alliance on Whiteout Survival State 1604, it is now available for anyone to use for their own needs. The tool collects the latest gift codes from both online sources and a local gift_code.csv database, merging them into a single list. It redeems all gift codes for all members, but first checks the validity of each code to avoid using expired ones. To prevent being blocked by the API endpoint, the tool waits a few seconds before redeeming the next code. It can be scheduled to run daily using a cron job.

## System Requirements
* Python (recommended 3.12.X, minimal 3.4.X)
* Works for MacOS, Linux and Windows

### Files
The program relies on two CSV files:
1. members.csv
2. gift_codes.csv

Both files must be provided via the constants MEMBERS_CSV and GIFT_CODES_CSV. As stated in the code, these files can also be located at a publicly accessible remote location. By default, the local CSV files inside the "input" folder will be loaded.

Before running the program, ensure that all user IDs are stored in the "./input/members.csv" file.
Custom gift codes can be added via the "./input/gift_codes.csv" file.

#### Template gift_codes.csv
```csv
  ID
  GiftCode1
  GiftCode2
```
#### Template members.csv
```csv
  ID,Username
  1111111,User1
  2222222,User2
```

Currently, the username feature is not actively used. A future version of the tool will support checking for changed usernames.

**Info: To temporarily skip a user from being processed, add a leading # to the user's ID.**

## Run Locally
If you know how to run a Python program, you can skip the steps below and do it your way; otherwise, follow this tutorial.

1. Clone the project
```bash
  git clone https://github.com/makorus/pyWoSRedemptionTool.git
```

2. Go to the project directory
```bash
  cd pyWoSRedemptionTool
```

3. Create new Python Virtual Environment
```bash
   python3.12 -m venv .venv
```

4. Activate Python Virtual Environment
```bash
   source .venv/bin/activate
```

5. Install dependencies
```bash
  pip install -r requirements.txt
```

6. Deactivate Python Virtual Environment
```bash
  deactivate
```

7. Run the program
```bash
  .venv/bin/python main.py
```
