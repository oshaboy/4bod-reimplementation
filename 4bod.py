import sys,time,re
from PIL import Image
IP = 0
program = []
VRAM = [[False for i in range(16)] for j in range(16)]
def print_VRAM():
    for y in range(16):
        for x in range (16):
            print(x,y,VRAM[x][y],end=" ")

        print()
    print()
    print()
mem = [0] * 16
flags = [None] * 16
acc = 0
skip=False
exited=False
prg_limit=768
pygame_display_surface=None
def bound():
    global acc,IP
    acc %= 16


def nop():
    pass


def ldm():
    global acc,IP
    IP += 1
    acc = mem[program[IP]]


def ldi():
    global acc,IP
    IP += 1
    acc = program[IP]


def set_to_arrow_state_keyboard():
    global acc
    acc=0
    if(keyboard.is_pressed("left")):
        acc+=1
    if (keyboard.is_pressed("right")):
        acc+=2
    if (keyboard.is_pressed("up")):
        acc+=4
    if (keyboard.is_pressed("down")):
        acc+=8


def set_to_arrow_state_curses():
    global acc,curses_screen


    acc = 0
    cur_key=curses_screen.getch()
    while(cur_key!=-1):
        if (cur_key==curses.KEY_LEFT):
            acc += 1
        if (cur_key==curses.KEY_RIGHT):
            acc += 2
        if (cur_key==curses.KEY_UP):
            acc += 4
        if (cur_key==curses.KEY_DOWN):
            acc += 8
        cur_key=curses_screen.getch()
def set_to_arrow_state_pygame():
    global acc


    acc = 0
    key_states=pygame.key.get_pressed()
    if (key_states[pygame.K_LEFT]):
        acc += 1
    if (key_states[pygame.K_RIGHT]):
        acc += 2
    if (key_states[pygame.K_UP]):
        acc += 4
    if (key_states[pygame.K_DOWN]):
        acc += 8
def stm():
    global acc,IP
    IP += 1
    mem[program[IP]] = acc


def inc():
    global acc,IP
    acc += 1


def cls():
    global VRAM
    VRAM = [[False for i in range(16)] for j in range(16)]


def shl():
    global acc,IP
    acc *= 2


def shr():
    global acc,IP
    acc /= 2


def set_VRAM():
    global acc,IP
    IP += 2
    Y = mem[program[IP]]
    X = mem[program[IP - 1]]
    acc = VRAM[X][Y]+0 #quick and dirty bool to int conversion


def flip_VRAM():
    global acc,IP
    IP += 2
    Y = mem[program[IP]]
    X = mem[program[IP - 1]]
    #print_VRAM()
    VRAM[X][Y] = not VRAM[X][Y]


def flag():
    global acc,IP
    IP += 1
def jump():
    global acc,IP,flags
    if flags[mem[program[IP+1]]]==None:
        print("Flag {} Undefined".format(mem[program[IP+1]]))
        sys.exit(2)
    IP=flags[mem[program[IP+1]]]+1
def do_when_equal():
    global skip, acc, IP
    IP+=1
    skip=mem[program[IP]] != acc

def do_when_greater():
    global skip, acc, IP
    IP+=1
    skip=mem[program[IP]]<=acc
def do_when_less():
    global skip, acc, IP
    IP+=1
    skip=mem[program[IP]]>=acc
instructions=[nop,ldm,stm,ldi,set_to_arrow_state_pygame,inc,cls,shl,shr,set_VRAM,flip_VRAM,flag,jump,do_when_equal,do_when_greater,do_when_less]
instruction_sizes=[1,2,2,2,1,1,1,1,1,3,3,2,2,2,2,2]
def draw_screen_ansi():
    out_string="\033[H\033[2J" #clear screen
    pixels=("  ","██")
    for y in range(16):
        for x in range (16):
            out_string+=pixels[VRAM[x][y]]
        out_string+="\n"
    out_string+="\n"
    print(out_string)
def draw_screen_curses():
    global curses_screen
    curses_screen.erase()
    pixels=("  ","██")
    for y in range(16):
        for x in range (16):
            if (VRAM[x][y]):
                curses_screen.addstr(y,x*2,"██")

    curses_screen.refresh()
def draw_screen_pygame():
    global pygame_display_surface
    pygame_display_surface.fill((255,255,255))
    for y in range(16):
        for x in range(16):
            if (VRAM[x][y]==True):
                pygame.draw.rect(pygame_display_surface,(0,0,0), pygame.Rect(40*x,40*y,40,40))
    pygame.display.flip()

    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            sys.exit()

def draw_screen_tkinter():
    pass
def log_machine_state(logfile):
    global acc, IP
    loginfo="\n"
    loginfo+="Acc: {}\n".format(acc)
    loginfo+="Memory: ["
    for i in range(16):
        loginfo+=str(mem[i])
        if (i<15):
            loginfo+=", "
    loginfo+="]\n"
    loginfo += "IP: {} (next program nybbles:{} {} {})\n".format(IP,program[IP],program[(IP+1)],program[(IP+2)])
    logfile.write(loginfo)

def main(source_filename,logfilename="4bod.log", engine="pygame"):
    global instructions,IP,skip,program,pygame_display_surface
    # load program
    logfile=open(logfilename,"w")
    if (engine=="pygame"):
        import pygame
        global pygame
        pygame.init()
        instructions[4]=set_to_arrow_state_pygame
        pygame.display.init()
        pygame.display.set_mode((640,640))
        pygame_display_surface=pygame.display.get_surface()
    elif (engine=="ansi"):
        import keyboard
        global keyboard
        instructions[4]=set_to_arrow_state_keyboard
    elif (engine=="curses"):
        import curses
        global curses,curses_screen
        curses_screen=curses.initscr()
        curses.cbreak()
        stdscr.keypad(True)
    elif (engine=="tkinter" or engine=="tk"):
        import tkinter
        global tkinter, TK_Screen
        instructions[4] = set_to_arrow_state_tkinter
        TK_Screen=tkinter.Tk()

    else:
        print("Only Engines supported are pygame and ansi")
        sys.exit()


    source_file_raw=open(source_filename,"rb")
    first_3_bytes=source_file_raw.read(3)
    if (first_3_bytes[0]==ord("P") and first_3_bytes[1]==ord("1") and first_3_bytes[2]==ord("\n")):
        source_file_raw.close()
        source_file_raw=open(source_filename,"rt")
        line=source_file_raw.readline()
        if (line!="P1\n"):
            print("TF?")
            sys.exit()
        found=False
        while not found:
            line=source_file_raw.readline()
            if (line[0]=="#" or line==""):
                continue
            elif(re.match(r"^12\s+256$",line)==None): #if the image isn't the right size
                print("Image must be 12x256")
                sys.exit()
            else:
                found=True
                break
        the_rest=source_file_raw.read(-1)
        the_rest=re.sub(r"#[^\n]*","",the_rest)
        the_rest=the_rest.replace("\n","")
        the_rest=the_rest.replace("\r","")
        the_rest=the_rest.replace(" ","")
        the_rest=the_rest.replace("\t","")
        counter=0
        logfile.write("Program Listing: \n")
        while(the_rest!="" and the_rest!=None):
            program.append(int(the_rest[:4],2))
            logfile.write(the_rest[:4]+"\n")
            the_rest=the_rest[4:]
            counter+=1
        if (counter!=768):
            print("Pixel Data doesn't match dimensions")
            sys.exit()






    else:
        source_image=Image.open(source_filename).convert("1")
        source_image_dump = source_image.load()
        if (source_image.width != 12 or source_image.height != 256):
            print("Image must be 12x256")
            sys.exit()
        counter=0
        logfile.write("Program Listing: \n")
        for y in range(256):
            for x in range(0,12,4):

                cur_nybble=0
                if  source_image_dump[(x+3,y)] == 0:
                    cur_nybble+=1
                if  source_image_dump[(x+2,y)] == 0:
                    cur_nybble+=2
                if  source_image_dump[(x+1,y)] == 0:
                    cur_nybble+=4
                if  source_image_dump[(x+0,y)] == 0:
                    cur_nybble+=8
                counter+=1
                program.append(cur_nybble)
                logfile.write(str(cur_nybble)+"\n")



    #find flags
    cur_nybble_ptr=0
    while (cur_nybble_ptr<prg_limit):
        if program[cur_nybble_ptr]==11:
            flags[program[cur_nybble_ptr+1]]=cur_nybble_ptr
        cur_nybble_ptr+=instruction_sizes[program[cur_nybble_ptr]]
    logfile.write(str(flags))
    try:
    #interpreter
        while (not exited):
            IP=0
            while (IP<prg_limit):
                if program[IP]!=0:
                    log_machine_state(logfile)
                if (not skip):
                    instructions[program[IP]]()
                    IP+=1

                else:
                    if (program[IP]!=0):
                        skip=False
                    IP+=instruction_sizes[program[IP]] 
                bound()
            #sys.exit()
            logfile.write("\nDrawing screen\n")
            if (engine=="pygame"):
                draw_screen_pygame()
            elif (engine=="ansi"):
                draw_screen_ansi()
            elif (engine=="tkinter" or engine=="tk"):
                draw_screen_tkinter()
            elif (engine=="curses"):
                draw_screen_curses()
            time.sleep(0.05)

    except KeyboardInterrupt:
        if (engine=="curses"):
            curses.endwin()
        return



if __name__ == "__main__":
    if (len(sys.argv)>2):
        if (sys.argv[2]=="-ansi"):
            main(sys.argv[1],engine="ansi")
        elif(sys.argv[2]=="-pygame"):
            main(sys.argv[1],engine="pygame")
        elif(sys.argv[2]=="-tk"):
            print("Unimplemented")
            #main(sys.argv[1],engine="tk")
        elif(sys.argv[2]=="-curses"):
            print("Unimplemented")
            #main(sys.argv[1],engine="curses")

    else:
        main(sys.argv[1])
