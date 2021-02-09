from notebook.auth import passwd
import random
import os

random.seed()

password = '{:08d}'.format(random.randint(0,1e8))
password_encrypted = passwd(password)

command = (
    "jupyter"
    " notebook"
    " --NotebookApp.allow_origin=$(gp url 8888)"
    " --ip=*"
    " --NotebookApp.password='{}'".format(password_encrypted)
)

print('\n\nIn the Open Ports tab, click <Make Public> and <Open Browser>.\n\nThe Jupyter password is {}\n\n'.format(
    password
))

os.system(command)
