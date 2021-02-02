import sys

def process_file(file_name, results):
    with open(file_name, "r") as file:
        for line in file:
            if "(" in line and  ")" in line and "C901" in line:
                start = line.index("(") + 1
                end = line.index(")")
                try:
                    results[line[:start-1]] = int(line[start:end])
                except ValueError:
                    pass


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Requires two file names of flake8 complexity output as parameters.\n python <script> <old> <new>")
        exit(1)

    old = {}
    new = {}
    process_file(sys.argv[1], old)
    process_file(sys.argv[2], new)

    delta = {}
    for match in (old.keys() & new.keys()):
        if old[match] < new[match]:
            delta[match] = f"+{new[match] - old[match]}"

    for extra in (new.keys() ^ (old.keys() & new.keys())):
        delta[extra] = f"+{new[extra]}"

    if len(delta) > 0:
        for key, value in delta.items():
            print(f"{key} ({value})")
        exit(1)

    exit(0)