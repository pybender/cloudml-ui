import os
import sys
import site


sys.stdout = sys.stderr


def add_to_path(dirs):
    prev_sys_path = list(sys.path)

    for directory in dirs:
        site.addsitedir(directory)

    new_sys_path = []
    for item in list(sys.path):
        if item not in prev_sys_path:
            new_sys_path.append(item)
            sys.path.remove(item)
    sys.path[:0] = new_sys_path


add_to_path([
    '{{ env_path }}/lib/python2.6/site-packages',
    '{{ env_path }}/lib/python2.7/site-packages',
    '{{ env_path }}/src',
    '{{ project_path }}',
    '{{ django_path }}',
])


os.environ['USER'] = '{{ user }}'

from api import app as application
