import sys
import os.path
import time

def main(argv):
    txtFile = argv[0]

    results = []
    f = open(txtFile, "r")
    text = f.read()
    index = 0
    for i in range(6):
        if ((text.find("FAIL", index) < text.find("PASS", index) and text.find("FAIL", index) != -1)) or text.find("PASS", index) == -1):
            results.append("FAIL")
            index = text.find("FAIL", index) + 4
        else:
            results.append("PASS")
            index = text.find("PASS", index) + 4
    f.close()

    f = open(txtFile, "w")
    f.write("Unfair - At least one lasso: " + results[0] + "\n")
    f.write("Unfair - Can reach termination: " + results[1] + "\n")
    f.write("OBE - No lasso: " + results[2] + "\n")
    f.write("HSA - No lasso: " + results[3] + "\n")
    f.write("OBE+HSA - No lasso: " + results[4] + "\n")
    f.write("LOBE - No lasso: " + results[5] + "\n")
    
    
    return 0
               
      
if __name__ == "__main__": 
  
    # calling main function 
    main(sys.argv[1:])