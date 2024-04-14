import pytest, project, os
from datetime import datetime

PROJECT_PATH = os.getcwd()
PDFFILENAME = f"{PROJECT_PATH}/attendance.pdf"
TODAY = datetime.now().strftime('%m/%d/%Y')

def test_yesno(): # check top see if this returns true when given correct input, if not it goes into an infinite loop
        project.input = lambda _: 'y'
        assert project.yesno("yes or no?") == True
def test_getInt(): #same as above
        project.input = lambda _: '1'
        assert project.getInt("m",[0,5]) == True

def teardown_method(self, method):
        project.input = input

def test_verifyEmail():
      assert project.verifyEmail("billy@luxelab.com") == True

def test_verifyEmail_incorrect():
       assert project.verifyEmail("CAT@DOG") == False

def test_printLogo():
    response = """
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
    assert project.printLogo() == response

def test_createPDF():
        atten = [{'date': '2024/04/01', 'role': '0', 'name': 'Billy', 'service': 'Cutting'}, {'date': '2024/04/01', 'role': '0', 'name': 'Aimee', 'service': 'Color'}, {'date': '2024/04/01', 'role': '1', 'name': 'Coco', 'service': 'Cut'}, {'date': '2024/04/01', 'role': '1', 'name': 'Dayne', 'service': 'Single Process'}, {'date': '2024/04/01', 'role': '1', 'name': 'Saman', 'service': 'Highlights'}, {'date': '2024/04/01', 'role': '1', 'name': 'Lisa', 'service': 'Blow-Dry'}, {'date': '2024/04/01', 'role': '1', 'name': 'Bob', 'service': 'Cut'}, {'date': '2024/04/01', 'role': '0', 'name': 'David', 'service': 'Cutting'}, {'date': '2024/04/01', 'role': '1', 'name': 'Sarah', 'service': 'Highlights'}, {'date': '2024/04/02', 'role': '1', 'name': 'Toledo', 'service': 'Absent'}]
        project.createPDF(atten)
        assert os.path.exists(PDFFILENAME)
