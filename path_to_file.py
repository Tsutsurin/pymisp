import os
import glob


def path_to_txt():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    file_ = glob.glob(os.path.join(current_directory, 'id.txt'))
    if not file_:
        file = open('id.txt', 'w')
        file.close()
    return file_[0]

def path_to_log():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    file_ = glob.glob(os.path.join(current_directory, 'application.log'))
    if not file_:
        file = open('application.log', 'w')
        file.close()
    return file_[0]
