import os
from os.path import join, exists

def get_file_lines(file_path):
    with open(file_path, "r") as f:
        file_lines = f.read().splitlines()
    # Cleans by removing metadata tags from the list of lines
    file_lines = [x for x in file_lines if not x.startswith(";")]
    return file_lines

# from https://stackoverflow.com/questions/19859282/
def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

# Returns true if there are any numerical digits (0-9) in the lines; false otherwise
def check_for_digits(lines):
    for line in lines:
        if hasNumbers(line):
            return True
    # Searched all lines and didn't find any numbers
    return False

def main():
    data_path = join(os.getcwd(), "local_data", "trl")
    transcript_file_paths = []
    for transcript in os.listdir(data_path):
        transcript_file_paths.append(join(data_path, transcript))

    for transcript_file in transcript_file_paths:
        file_lines = get_file_lines(transcript_file)
        if check_for_digits(file_lines):
            print(transcript_file + " contains digits")
    print("Done checking")


if __name__ == "__main__":
    main()
