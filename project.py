import sys, csv, subprocess, re, getpass, smtplib, os
from email.message import EmailMessage
from fpdf import FPDF
from datetime import datetime

ListOfSercvices = ["Cutting", "Cutting Shadow", "Color", "Color Shadow", "Theory"]
ListOfTeachers = ["Cut", "Styling", "Single Process", "Balayage", "Highlights", "Dollhead", "Absent"]

PROJECT_PASSWORD = os.getenv("PROJECT_PASSWORD")
PROJECT_USERNAME = os.getenv("PROJECT_EMAIL")
PROJECT_PATH = os.getcwd()
CSVFILE = f"{PROJECT_PATH}/attendance.csv"
PDFFILENAME = f"{PROJECT_PATH}/attendance.pdf"
#LOGOFILE = f"{PROJECT_PATH}/logo.txt"
TODAY = datetime.now().strftime("%m/%d/%Y")

# i need to pass the file around but do not want to have to put in all of my function calls
# so im just declaring it as an empty variable and relying on the fact that python is loose
# with typing
outfile = None


class attendancePDF(FPDF):
    def header(self):  
        self.set_font('Times', size=24)
        self.set_text_color(0,0,0)        
        # Calculate the position to center the image
        image_width = 20  
        page_width = self.w - 2 * self.l_margin
        x_pos = (page_width - image_width) / 2
        self.image("luxelab.png", x=x_pos) #logo
        self.ln(20) 
        self.cell(text=f"luxelab Attendance {TODAY}",align="C", center=True)        
        self.ln(20) 

def main():
    global outfile
    
    # before proceeding any further make sure the file exists in case the user types -r maliciously
    try:
        outfile = open(CSVFILE,mode="r")
    except FileNotFoundError:
        Initialize() # if the CSV file doesnt exist, create it and write headers
    logo = printLogo()    

    # check to see if the "resume" flag has been set, if so, load values from the existing file and return
    # as a list of dictionaries

    try:
        if len(sys.argv) == 1:
            clearTerminal()
            print(logo + "\n          luxelab attendance\n")
            attendance=[]
            input("Press enter to continue...")
            outfile = open(CSVFILE,mode="a")
            mainMenu(attendance, logo=logo)
        elif len(sys.argv) == 2 and sys.argv[1] in ("-r", "--resume"):
            clearTerminal()
            print(logo + "\n          luxelab attendance\n")
            attendance = ResumeSession()
            input("Press enter  to continue...")
            outfile = open(CSVFILE,mode="a")
            mainMenu(attendance, logo=logo)
        else:
            sys.exit(f"Incorrect usage.\nCorrect usage: 'attendance [-r|--resume]'\nUse -r or --resume to resume a crashed or terminated session.")
    except EOFError:
        clearTerminal()
        # save data in memory to CSV just in case
        rewriteCSV(attendance)
        print(f"\nGoodbye! See you soon!!!!")
     
    # cleanup
    outfile.close
    clearTerminal()
    print(f"\nGoodbye! See you soon!!!!")
    
def mainMenu(attendance:list = [], logo:str = ""):
    
    attendance_sent = False
    
    menu = (f"1. Enter teacher\n"
        "2. Enter Student\n"
        "3. Delete an Entry\n"
        "4. Mail class Information\n"
        "5. Exit Program Without Saving\n")


    while True:
        # clear screen, Display Menu etc
        clearTerminal()
        print(logo)
        print(f"\nluxelab attendance: {TODAY}")
        print(f"-------------------------------------")
        
        if len(attendance) > 0:
            # only print if there are students
            print("Current Roster:")
            print(getRoster(attendance,nums=False))
            print(f"-------------------------------------")
        
        print(menu)
        choice = getInt("Select from the list of options: ", [1,6])

        match choice:
            case 1: # add a teacher
                teacher:dict = addEntry(0)
                if teacher:
                    writeRow(teacher)   # add to CSV in case of crash
                    attendance.append(teacher)  # add to the local copy in memory]
                    #rewriteCSV()
            case 2: # add a student
                student:dict = addEntry(1)
                if student:
                    writeRow(student)
                    attendance.append(student)
                    #rewriteCSV()
            case 3: # Delete an entry
                deleteEntry(attendance, logo)
            case 4: # create pdf and email
                if attendance == []:

                    input(f"\nThere is no information to send")
                else:

                    if createPDF(attendance):
                        if (attendance_sent := emailForm()):
                            return
                        else:
                            input("\nEmail not sent. Press enter to continue...")
                    else:
                        input("Error creating the pdf. Press enter to continue...")

            case 5: # exit
                if attendance_sent == True:
                    return True
                else:
                    if yesno("Attendance has not yet been submitted, are you sure (y/n)? "):
                        rewriteCSV(attendance)
                        return True
                    else:
                        continue
            case _:
                print("Invalid input. Please choose one of the menu options.")
                input()
                continue

        attendance.sort(key=lambda x: int(x['role']))    

def addEntry(entry_type: int)->dict:
    # 0 for teacher, 1 for student
    entry_types = ["teacher", "student"]
  
    if entry_type == 0:
        class_types = ["Cutting", "Cutting Shadow", "Color", "Color Shadow", "Theory"]
    else:
        class_types = ["Cut", "Styling", "Single Process", "Balayage", "Highlights", "Dollhead", "Absent"]
  
    entry_name = input(f"\nPlease enter the {entry_types[entry_type]}'s name: ")
    print(f"\nSelect a role: ")
    
    for i, TT in enumerate(class_types):
        print(f"{i+1}:", TT)
    service_type = getInt("Select one of the above options: ", [1,len(class_types)+1]) - 1
    if yesno(f"Are you sure you want to add {entry_name} as {class_types[service_type]}? "):
        return {"date": TODAY, "role": entry_type, "name": entry_name, "service": class_types[service_type]}
    else:
        return None       
    
def deleteEntry(attendance: list, logo:str):
    clearTerminal()
    print(logo + f"\n")
    
    if (length := len(attendance)) == 0:
        input("There are no entries to delete. Press enter to continue")
        return
    
    print(getRoster(attendance))
    attendance.sort(key=lambda x: int(x['role']))   #sort the list so that it is in the same order as the display, just in case
    
    try:
        toDelete = getInt("Which entry would you like to delete? (press ctl-d to cancel) ", [1, length+1])
    except EOFError:
        return
    
    if not (toDelete in range(1,length+1)):
        input("Invalid entry. Press enter to continue")
        return 
    else:
        if yesno(f"Are you sure you want to remove {attendance[toDelete - 1]['name']} y/n ") == True:
            del attendance[toDelete - 1]
            rewriteCSV(attendance)  # rewrite the CSV
            return 

def getRoster(attendance: list, nums=True)->str:
    ROLE = ["Teacher", "Student"]
    i = 1
    attendance_string = ""

    for row in sorted(attendance, key=lambda x: int(x['role'])): # attendance:
        if nums:
            attendance_string += f"{i}. {row['name']} - {ROLE[int(row['role'])]} - {row['service']}\n"
        else:
            attendance_string += f"* {row['name']} - {ROLE[int(row['role'])]} - {row['service']}\n"
        i += 1
    return  attendance_string

def createPDF(attendance: list)->bool:
    
    try:
        pdf = attendancePDF(orientation="portrait", format="A4")
        pdf.add_page()
        subText = getRoster(attendance)
        pdf.set_font('Times', "B", size=18)
        pdf.set_text_color(0,0,0)
        pdf.multi_cell(0,10,text=subText)
        pdf.output(PDFFILENAME)
        return True
    except ValueError:
        input("Woops. Problem creating the PDF")
        return False

def emailForm()->bool:
    
    print("\nPress CTL-D to go back")
    
    try:
        while True:
            if not (email_address := input("\nWhat is your email address? ")) or not verifyEmail(email_address):
                print("Invalid email address. Please try again.")
                continue            
            else:
                my_password = getpass.getpass("Please enter the password for this account: ")    
                break
    except EOFError:
        return False
    
    email_address = PROJECT_USERNAME # pull the actual password and username from the environment variables
    my_password = PROJECT_PASSWORD
    msg_content = f"Here is the attendance list for {TODAY}"

    msg = EmailMessage()
    msg['Subject'] = "Luxelab Class Attendance Report"
    msg['From'] = email_address
    msg['To'] = email_address
    msg.set_content(msg_content)

    smtp_port = 587
    smtp_server = "smtp.gmail.com"

    with open(PDFFILENAME, 'rb') as file:
        file_data = file.read()
    msg.add_attachment(file_data, maintype='application', subtype="pdf", filename=PDFFILENAME)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_address, my_password)
            server.send_message(msg)
        exit_message = f"Attendance successfully sent from {email_address}.\nThanks for being a part of the luxelab team!\n"
        input(exit_message)
        return True      
    except Exception as e:
        input(f"There was an error emailing the file.\n{e}")
        return
 
def writeRow(row: dict):
    global outfile
    writer = csv.DictWriter(outfile, fieldnames=["date", "role", "name", "service"])
    writer.writerow(row)

def Initialize():
    global outfile
    outfile = open(CSVFILE,mode="w")
    outfile.write(f"date,role,name,service\n")
    outfile.close

def ResumeSession()->list:
    global outfile
    attendance_list = []
    outfile = open(CSVFILE, "r")
    reader = csv.DictReader(outfile)

    for row in reader:
        attendance_list.append(row)
        
    if attendance_list == []:
        print("No previous records found")
        return []
    else:
        print("Previous session loaded...")
        return attendance_list

def rewriteCSV(attendance:list):
    Initialize()
    writer = csv.DictWriter(outfile, fieldnames=["date", "role", "name", "service"])
    for line in attendance:
        writer.writerow(line)
    return True

def printLogo()->str:
    logo= """
#####################################
#                                   #
#                #####              #
#                #####              #
#                #####              #
#                #####              #
#        ####################       #
#        ####################       #
#        ####################       #
#                #####              #
#                #####              #
#                #####              #
#                #####              #
#                                   #
#####################################"""
    return logo
    # logo = f""
    # with open(LOGOFILE, mode="r") as logofile:
    #     for line in logofile:
    #         logo += line
    #     return logo

def verifyEmail(email:str)->bool:
    regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(regex, email))

def clearTerminal():
    subprocess.run('cls' if subprocess.os.name == 'nt' else 'clear', shell=True)

def yesno(message:str):
    while True:
        response = input(message).lower()
        if response == "y":
            return True
        elif response == "n":
            return False
        else:
            continue

def getInt(m:str, intrange:list)->int:
    while True:
        try:
            n = int(input(m))
            if n in range(intrange[0],intrange[1]):
                return n
            else:
                print(f"Please select a number between {intrange[0]} and {intrange[1]}")
                continue
        except ValueError:
            print(f"Invalid input. Please enter a number between {intrange[0]} and {intrange[1]-1}")
            continue

if __name__ == "__main__":
    main()

# sample list of dicts 
#[{'date': '2024/04/01', 'role': '0', 'name': 'Billy', 'service': 'Cutting'}, {'date': '2024/04/01', 'role': '0', 'name': 'Aimee', 'service': 'Color'}, {'date': '2024/04/01', 'role': '1', 'name': 'Coco', 'service': 'Cut'}, {'date': '2024/04/01', 'role': '1', 'name': 'Dayne', 'service': 'Single Process'}, {'date': '2024/04/01', 'role': '1', 'name': 'Saman', 'service': 'Highlights'}, {'date': '2024/04/01', 'role': '1', 'name': 'Lisa', 'service': 'Blow-Dry'}, {'date': '2024/04/01', 'role': '1', 'name': 'Bob', 'service': 'Cut'}, {'date': '2024/04/01', 'role': '0', 'name': 'David', 'service': 'Cutting'}, {'date': '2024/04/01', 'role': '1', 'name': 'Sarah', 'service': 'Highlights'}, {'date': '2024/04/02', 'role': '1', 'name': 'Toledo', 'service': 'Absent'}]
