
from StreamMaster import *

from _utils import *

input_file_path = os.environ['IN_PROCESS_HIGHLIGHTS']
output_file_path = os.environ['PROCESSED_HIGHLIGHTS']

# Confirm which Highlight Reels have already been processed


# Confirm whether All the highlights have been pre-processed


# Complete production of the Highlights

if __name__ == '__main__':
    make_highlights_compilation(mysql_engine, input_file_path, output_file_path)