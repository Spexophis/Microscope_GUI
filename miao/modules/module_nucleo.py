import subprocess

com_port = 'COM4'
filename = r'C:\Users\Public\Documents\Github\Microscope_GUI\miao\modules\nucleo_board.py'

cmd = [
    'mpremote',
    'connect',
    com_port,
    'fs',
    'cp',
    filename,
    ':'
]


def send_trigger():
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print('Upload successful!')
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print('Upload failed!')
        print(e.stderr)
