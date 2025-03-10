import serial 
import pyTMCL
import configparser


def init():
    #read address of the motorboard from the config-file
    motor_pc_no = None
    address_motorboard = None
    this_config = configparser.ConfigParser()
    this_config.read('../../../this_pc.conf')
    if "who_am_i" in this_config:
        if this_config["who_am_i"]["type"]!="motor_pc":
            print("According to the 'this_pc.config'-file this pc is not meant as a motor pc! Please fix that!")
            exit()
        motor_pc_no = int(this_config["who_am_i"]["no"])
    else:
        print("There is no config file on this computer which specifies the computer function! Please fix that!")
        exit()
    global_config = configparser.ConfigParser()
    global_config.read('../global.conf')
    if "rate_transmission" in global_config:
        if motor_pc_no == 1:
            address_motorboard=global_config["motor_pc_1"]["address_motorboard"]
        elif motor_pc_no == 2:
            address_motorboard=global_config["motor_pc_2"]["address_motorboard"]
        else:
            print("Error in the 'this_pc.config'-file. The number of the Motor PC is neither 1 nor 2. Please correct!")
    else:
        print("Error in the 'this_pc.config'-file. The file does not contain the section 'rate_transmission'. Please correct!")
        exit()    
    #serial_port = serial.Serial("/dev/ttyUSB0",baudrate=9600,timeout=1)
    serial_port = serial.Serial(address_motorboard,timeout=.25)
    bus=pyTMCL.connect(serial_port)
    #bus.send(0,9,65,0,0)
    #print(bus.send(0,10,65,0,0).value)
    #print(serial_port.baudrate)
    module = bus.get_module(0)

    a=[]
    
    #map the ports of the board to the correct motors
    motor0=int(global_config["motor_pc_{}".format(motor_pc_no)]["motor0_port"])
    motor1=int(global_config["motor_pc_{}".format(motor_pc_no)]["motor1_port"])
    motor2=int(global_config["motor_pc_{}".format(motor_pc_no)]["motor2_port"])
    motor3=int(global_config["motor_pc_{}".format(motor_pc_no)]["motor3_port"])
    motor4=int(global_config["motor_pc_{}".format(motor_pc_no)]["motor4_port"])
    motor5=int(global_config["motor_pc_{}".format(motor_pc_no)]["motor5_port"])
    
    order=[motor0, motor1, motor2, motor3, motor4, motor5]
    for i in order:
        a.append(module.get_motor(i)) # 6 motoren eingefuegt
    print(order)
    for i in order:
        if i>=4:
            a[i].set_axis_parameter(5,1000)  # acceleration einstellen
        else:
            a[i].set_axis_parameter(5,500)  # acceleration einstellen
        
    #a[3].set_pullups(3) #disable pullups for Mirror motors
    
    for i in range (4):
        a[i].set_axis_parameter(140,5) #32 Microsteps
        a[i].axis.left_limit_switch_disabled=False  #enable limit switches
        a[i].axis.right_limit_switch_disabled=False

    for i in range (4,6):
        a[i].set_axis_parameter(140,4) #16 Microsteps
        a[i].axis.left_limit_switch_disabled=False  #enable limit switches
        a[i].axis.right_limit_switch_disabled=False
    
    for i in range (6):
        a[i].set_axis_parameter(191,0) #PWM frequency
        a[i].set_axis_parameter(192,1) #PWM autoscale
        a[i].set_axis_parameter(7,0) #no standby current
        a[i].set_axis_parameter(186,0) #SC threshold - need to activte "StealthChop"for 204
        a[i].set_axis_parameter(187,15) #SC gradient
        a[i].set_axis_parameter(204,2) #short coils when no drive -> will hold position
    
        a[i].set_axis_parameter(24,0) #1: invert right endswitch status
        a[i].set_axis_parameter(25,0) #1: invert left endswitch status
        #print(i,a[i].axis.get(24),a[i].axis.get(25))
    
    #reduce max drive current
    #current can set in 32 steps, 0..7 = first step = 0.06A .. 248..255 = last step = 1.915A
    a[0].set_axis_parameter(6,127) #120...127 15 Peak: 1.354A RMS: 0.958A
    a[1].set_axis_parameter(6,127)
    a[2].set_axis_parameter(6,127)
    a[3].set_axis_parameter(6,255) #248...255 31 Peak: 2.708A RMS: 1.915A
    a[4].set_axis_parameter(6,63) #56...63 7 Peak: 0.677A RMS: 0.479A
    a[5].set_axis_parameter(6,63)
    a[4].set_axis_parameter(14,1) #1: swap limit switches
    a[5].set_axis_parameter(14,1)
    a[0].set_axis_parameter(14,1)
    a[1].set_axis_parameter(14,1)
    a[2].set_axis_parameter(14,1)
    a[3].set_axis_parameter(14,1)
    
    # Reference search direction settings
    a[0].set_axis_parameter(193,1) #1: Left Ref Search 65: Right Ref Search
    a[1].set_axis_parameter(193,1)
    a[2].set_axis_parameter(193,1)
    a[3].set_axis_parameter(193,1)
    a[4].set_axis_parameter(193,1)
    a[5].set_axis_parameter(193,1)
    #why no mirrors here? I assume 1 is default so also set there
    
    #max speed
    a[0].axis.max_positioning_speed=15000
    a[0].set_axis_parameter(194, 15000)
    a[0].set_axis_parameter(195, 5000)

    a[1].axis.max_positioning_speed=15000
    a[1].set_axis_parameter(194, 15000)
    a[1].set_axis_parameter(195, 5000)
    
    a[2].axis.max_positioning_speed=15000
    a[2].set_axis_parameter(194, 15000)
    a[2].set_axis_parameter(195, 5000)
    
    a[3].axis.max_positioning_speed=45000 #Not too fast, otherwise torque drops
    a[3].set_axis_parameter(194, 45000) #Refsearch Speed of Mirror Height
    a[3].set_axis_parameter(195, 5000)
    
    a[4].set_axis_parameter(194, 5000) #search speed
    a[4].set_axis_parameter(195, 1000) # switch speed
    
    a[5].set_axis_parameter(194, 5000)
    a[5].set_axis_parameter(195, 1000)
    
    a[4].axis.max_positioning_speed=5000
    a[5].axis.max_positioning_speed=5000
    
    return a, serial
    

def ismoving(themotor):
    var=themotor.get_position_reached()
    if var<=1:
        return 1-var
    else:
        return ismoving(themotor)
def position(themotor):
    return themotor.axis.get(1)
