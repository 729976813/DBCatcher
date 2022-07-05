import os

def get_files(root_dir):
    '''
    :param root_dir:
    :return:
    '''
    root_dir = [root_dir]
    files = []
    while root_dir:
        for dir in root_dir:
            dirs_or_files = os.listdir(dir)
            dir_or_file = os.path.join(dir, dirs_or_files[0])
            root_dir.remove(dir)
            if os.path.isdir(dir_or_file):
                for sub_dir in dirs_or_files:
                    root_dir.append(os.path.join(dir, sub_dir))
            else:
                for file in dirs_or_files:
                    files.append(os.path.join(dir, file))
    return files


def get_dirs(root_dir):
    '''
    :param root_dir:
    :return:
    '''
    root_dir_list = [root_dir]
    dirs = []
    for dir in root_dir_list:
        dirs_or_files = os.listdir(dir)
        dir_or_file = os.path.join(dir, dirs_or_files[0])
        if os.path.isdir(dir_or_file):
            root_dir_list.remove(dir)
            dirs.extend([os.path.join(dir, item) for item in dirs_or_files])
    return dirs


