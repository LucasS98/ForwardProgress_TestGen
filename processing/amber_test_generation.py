# -----------------------------------------------------------------------
# amber_two_generation.py
# Author: Hari Raval
# -----------------------------------------------------------------------
import sys
import re
from configuration import Configuration

# default Configuration object to be used in the Amber test generation
#default_config = Configuration(timeout=20000, workgroups=65535, threads_per_workgroup=1)


# write the necessary "boiler plate" code to generate an amber test, along with a Shader
# Storage Buffer Object with a memory location, workgroup size, and global variable to
# assign thread IDs. output is the file being written to and timeout determines (in ms) when the
# program will terminate in the case the GPU hangs
def write_amber_prologue(output, timeout, threads_per_workgrup):
    output.write("#!amber\n")
    output.write("\n")
    output.write("SET ENGINE_DATA fence_timeout_ms " + str(timeout) + "\n")
    output.write("\n")
    output.write("SHADER compute test GLSL\n")
    output.write("#version 430\n")
    output.write("\n")
    output.write("layout(set = 0, binding = 0) volatile buffer TEST {\n")
    output.write("\tuint x;\n")
    output.write("\tuint counter;\n")
    output.write("} test; \n")
    output.write("\n")
    output.write("layout(local_size_x = " + str(threads_per_workgrup) + ", local_size_y = 1, local_size_z = 1) in;\n")
    output.write("\n")
    output.write("void main()\n")
    output.write("{\n")
    output.write("\tuint gid_x = gl_GlobalInvocationID.x;\n")
    output.write("\tint pc = 0;\n")
    output.write("\n")


# write the appropriate content to set up each thread by using the thread_instructions, the thread_number, and
# the total number of instructions (instruction_count)
def write_amber_thread_program(output, thread_instructions, thread_number, instruction_count):
    output.write("\tif (gid_x == " + str(thread_number) + ") { \n")
    output.write("\t   int terminate = 0;\n")
    output.write("\n")
    output.write("\twhile (true) {\n")
    output.write("\t   if (terminate == 1) {\n")
    output.write("\t   break;\n")
    output.write("\t}\n")
    output.write("\tswitch(pc) {\n")
    output.write("\n")

    program_end = len(thread_instructions)

    # iterate over each instruction assigned to the specific thread and generate the test case
    for instruc_id, instruction in enumerate(thread_instructions):
        write_amber_thread_instruction(output, instruction, instruc_id, instruction_count)

    output.write("\t  case " + str(program_end) + ":\n")
    output.write("\t\tterminate = 1;\n")
    output.write("\t\tbreak;\n")
    output.write("\n")
    output.write("\t     }\n")
    output.write("\t   }\n")
    output.write("\t}\n")
    output.write("\n")


# write the appropriate test cases for each instruction based off of the instruction id and number of instructions
def write_amber_thread_instruction(output, instruction, instruc_id, instruction_count):
    pattern = "\\((.+?)\\)"
    search_pattern = re.search(pattern, instruction)
    numerical_representation = " "
    if search_pattern:
        numerical_representation = search_pattern.group(1)

    # create a list of the arguments that are provided from the pseudo instruction
    numerical_representation = numerical_representation.split(",")

    # note the memory_location is not needed in current implementation
    memory_location = numerical_representation[0]

    output.write("\t  case " + str(instruc_id) + ": \n")

    # extract the appropriate values for an atomic exchange branch from the numerical_representation of the instruction
    # and call handle_atomic_exchange_branch
    if instruction.startswith("atomic_exch_branch"):
        check_value = numerical_representation[1]
        exchange_value = numerical_representation[2]
        instruction_address = numerical_representation[3]
        handle_atomic_exchange_branch(output, check_value, exchange_value, instruction_address, instruction_count)

    # extract the appropriate values for an atomic exchange branch from the numerical_representation of the instruction
    # and call handle_amber_check_branch
    elif instruction.startswith("atomic_chk_branch"):
        check_value = numerical_representation[1]
        instruction_address = numerical_representation[2]
        handle_amber_check_branch(output, check_value, instruction_address, instruction_count)

    # extract the appropriate values for an atomic exchange branch from the numerical_representation of the instruction
    # and call handle_atomic_store
    elif instruction.startswith("atomic_store"):
        write_value = numerical_representation[1]
        handle_atomic_store(output, write_value)


# write the amber test code for an atomic exchange branch instruction
def handle_atomic_exchange_branch(output, check_value, exchange_value, instruction_address, instruction_count):
    output.write("\t\tif (atomicExchange(test.x, " + exchange_value + ") ==  " + check_value + ") { \n")
    if instruction_address == "END":
        output.write("\t\t   pc = " + str(instruction_count) + ";\n")
    elif instruction_address != "END":
        output.write("\t\t   pc = " + instruction_address + ";\n")
    else:
        print("Incorrect instruction_address in handle_amber_check_branch")
        exit(1)

    output.write("\t\t}\n")
    output.write("\t\telse {\n")
    output.write("\t\t   pc = pc + 1;\n")
    output.write("\t\t}\n")
    output.write("\t\tbreak;\n")
    output.write("\n")


# write the amber test code for an atomic check branch instruction
def handle_amber_check_branch(output, check_value, instruction_address, instruction_count):
    output.write("\t\tif (atomicAdd(test.x, 0) == " + check_value + " ) { \n")
    if instruction_address == "END":
        program_end = int(instruction_count) - 1
        output.write("\t\t   pc = " + str(program_end) + ";\n")
    elif instruction_address != "END":
        output.write("\t\t   pc = " + instruction_address + ";\n")
    else:
        print("Incorrect instruction_address in handle_amber_check_branch")
        exit(1)

    output.write("\t\t}\n")
    output.write("\t\telse {\n")
    output.write("\t\t   pc = pc + 1;\n")
    output.write("\t\t}\n")
    output.write("\t\tbreak;\n")
    output.write("\n")


# write the amber test code for an atomic store instruction
def handle_atomic_store(output, write_value):
    output.write("\t\tatomicExchange(test.x, " + write_value + ");\n")
    output.write("\t\tpc = pc + 1;\n")
    output.write("\t\tbreak;\n")
    output.write("\n")


# write the necessary "boiler plate" code to end the amber test, along with generating a desired number of threads
def write_amber_epilogue(output, workgroups, threads_per_workgroup):
    thread_test = int(workgroups) * int(threads_per_workgroup)

    output.write("\tatomicAdd(test.counter, 1);\n")
    output.write("}\n")
    output.write("END\n")
    output.write("\n")
    output.write("BUFFER tester DATA_TYPE uint32 SIZE 2 FILL 0\n")
    output.write("\n")
    output.write("PIPELINE compute test_pipe\n")
    output.write("  ATTACH test\n")
    output.write("  BIND BUFFER tester AS storage DESCRIPTOR_SET 0 BINDING 0 \n")
    output.write("\n")
    output.write("END\n")
    output.write("\n")
    output.write("RUN test_pipe " + str(workgroups) + " 1 1\n")
    output.write("EXPECT tester IDX 4 EQ " + str(thread_test) + "\n")


# generate an amber test with a provided input file, a desired output file name, and a Configuration object to set up
# the number of workgroups, threads per workgroup, and timeout
def generate_amber_test(inputted_file, output_file_name):
    input_file = inputted_file
    timeout = 20000

    if output_file_name.endswith(".amber"):
        print("Script will include the .amber extension, please provide a different output file name")
        exit(1)

    with open(input_file, 'r') as file:
        data = file.read().replace('\n', ' ')

    data_list = data.split(" ")

    while "" in data_list:
        data_list.remove("")

    instructions = []

    # iterate over each of the items from input and make a list of lists, where each list contains instructions for an
    # individual thread
    for index, item in enumerate(data_list):
        if item.startswith("THREAD"):
            temp_list = []
            temp_index = index + 1
            while temp_index < len(data_list) and not data_list[temp_index].startswith("THREAD"):
                temp_list.append(data_list[temp_index])
                temp_index = temp_index + 1
            instructions.append(temp_list)

    instruction_count = len(instructions)

    # name and open the output file to contain the amber test case
    output_amber_file = output_file_name
    output_amber_file = output_amber_file + ".amber"
    output = open(output_amber_file, "a")

    threads_per_workgroup = 1
    workgroups = 65535

    # call the appropriate functions to generate the amber test
    write_amber_prologue(output, timeout, threads_per_workgroup)

    for number, each_thread in enumerate(instructions):
        write_amber_thread_program(output, each_thread, number, instruction_count)

    write_amber_epilogue(output, workgroups, threads_per_workgroup)


def main():
    if len(sys.argv) != 3:
        print("Please provide a .txt file to parse and the desired name for the outputted Amber file")
        exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    # generate an amber test for the desired inputs, with a default configuration if none was provided
    generate_amber_test(input_file, output_file)


if __name__ == "__main__":
    main()
