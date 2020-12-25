#AppleBot

#library imports
import os
import subprocess
import re
import math
import importlib
import json
import threading
import shutil
from datetime import *
from random import *
from javax.swing import JFrame, JButton, JLabel, JScrollPane, JTextArea, JPanel, JButton
from java.awt.BorderLayout import *
from java.awt import Robot, Color
from sikuli import *

#basic sikuli configurations
Settings.ObserveScanRate = 10
Settings.MoveMouseDelay = 0
Settings.ActionLogs = 0
Settings.InfoLogs = 0
Settings.DebugLogs = 0

############################################################
 ######   #######  ##    ## ######## ####  ######    ######  
##    ## ##     ## ###   ## ##        ##  ##    ##  ##    ## 
##       ##     ## ####  ## ##        ##  ##        ##       
##       ##     ## ## ## ## ######    ##  ##   ####  ######  
##       ##     ## ##  #### ##        ##  ##    ##        ## 
##    ## ##     ## ##   ### ##        ##  ##    ##  ##    ## 
 ######   #######  ##    ## ##       ####  ######    ######  
############################################################

#in case ping latency is too high, increase the waiting time (use only integer values)
global walk_interval
walk_interval = 1

#center of screen (char's feet coordinates)
global screen_center_x
global screen_center_y
screen_center_x = 463
screen_center_y = 297

#tools
rope   = "o"  
shovel = "p"
ring   = "l"
amulet = "k"
food   = "u"

#spells
exana_pox = "i"
haste = "v"
utura = "5"
exeta_res = ["exeta res","6","atk",6]
min_to_box = 0
min_to_align = 1

#############################################################
########  ########  ######   ####  #######  ##    ##  ######  
##     ## ##       ##    ##   ##  ##     ## ###   ## ##    ## 
##     ## ##       ##         ##  ##     ## ####  ## ##       
########  ######   ##   ####  ##  ##     ## ## ## ##  ######  
##   ##   ##       ##    ##   ##  ##     ## ##  ####       ## 
##    ##  ##       ##    ##   ##  ##     ## ##   ### ##    ## 
##     ## ########  ######   ####  #######  ##    ##  ######  
#############################################################

#watchable regions
debuff_region     = Region(1111,451,110,15)
equip_region      = Region(1109,307,114,145)
battlelist_region = Region(1104,469,30,120)
game_region       = Region(226,124,474,348)
message_region    = Region(226,443,477,31)
action_bar_region = Region(1,482,925,40)

#############################################################################################
########  #### ##     ## ######## ##           ######   #######  ##        #######  ########  
##     ##  ##   ##   ##  ##       ##          ##    ## ##     ## ##       ##     ## ##     ## 
##     ##  ##    ## ##   ##       ##          ##       ##     ## ##       ##     ## ##     ## 
########   ##     ###    ######   ##          ##       ##     ## ##       ##     ## ########  
##         ##    ## ##   ##       ##          ##       ##     ## ##       ##     ## ##   ##   
##         ##   ##   ##  ##       ##          ##    ## ##     ## ##       ##     ## ##    ##  
##        #### ##     ## ######## ########     ######   #######  ########  #######  ##     ##
#############################################################################################

#returns the color (HEX) of one exact pixel on the screen
def pixelColor(posX,posY):   
    pixel = Robot().getPixelColor(posX,posY)
    r = pixel.getRed()
    g = pixel.getGreen() 
    b = pixel.getBlue() 
    color = '{:02x}{:02x}{:02x}'.format(r,g,b)
    return color

#to be used exclusively by the healer thread
def healerColor(posX,posY):
    pixel = Robot().getPixelColor(posX,posY)
    r = pixel.getRed()
    g = pixel.getGreen() 
    b = pixel.getBlue() 
    color = '{:02x}{:02x}{:02x}'.format(r,g,b)
    #print "Color at",posX,posY,":",color
    return color

###########################################################
##        #######   ######       #######  ######## ######## 
##       ##     ## ##    ##     ##     ## ##       ##       
##       ##     ## ##           ##     ## ##       ##       
##       ##     ## ##   ####    ##     ## ######   ######   
##       ##     ## ##    ##     ##     ## ##       ##       
##       ##     ## ##    ##     ##     ## ##       ##       
########  #######   ######       #######  ##       ##       
###########################################################

def logoff_function():
    
    if debuff_region.exists("battleon.png"):
        log("Battle icon on - Waiting 30 secs")
        attack_function()
        wait(30)
        log("Trying to logoff again...")
        logoff_function()
        
    else:
        log("Printing Screen")
        type("3", KeyModifier.CMD + KeyModifier.SHIFT)
        type("l", KeyModifier.CMD)
        log("[END OF EXECUTION]")
        closeFrame(0)

###########################################################################################
##      ##    ###    ##    ## ########   #######  #### ##    ## ######## ######## ########  
##  ##  ##   ## ##    ##  ##  ##     ## ##     ##  ##  ###   ##    ##    ##       ##     ## 
##  ##  ##  ##   ##    ####   ##     ## ##     ##  ##  ####  ##    ##    ##       ##     ## 
##  ##  ## ##     ##    ##    ########  ##     ##  ##  ## ## ##    ##    ######   ########  
##  ##  ## #########    ##    ##        ##     ##  ##  ##  ####    ##    ##       ##   ##   
##  ##  ## ##     ##    ##    ##        ##     ##  ##  ##   ###    ##    ##       ##    ##  
 ###  ###  ##     ##    ##    ##         #######  #### ##    ##    ##    ######## ##     ## 
###########################################################################################

#function to walk to next waypoint
def waypointer(label,wp):
    log("Walking to "+label+" waypoint "+str(wp)) 
    if label == "go_hunt":
        wp_action = imported_script.label_go_hunt(wp)
    
    if label == "hunt":
        wp_action = imported_script.label_hunt(wp)
        
    if label == "leave":
        wp_action = imported_script.label_leave(wp)

    #moves mouse back to center of screen 
    hover(Location(screen_center_x,screen_center_y))

    #checks if the Char has stopped or continues walking
    walking_check(0,wp_action,label,wp)
    
    return wp_action
 
def walking_check(time_stopped,wp_action,label,wp):
    while time_stopped != walk_interval:
        minimap_region    = Region(1109,161,115,119)
        minimap_region.onChange(1,changeHandler)
        minimap_region.somethingChanged = False
        minimap_region.observe(1)
        
        #if enters here, means char is still walking
        if minimap_region.somethingChanged:
            time_stopped = 0
            while debuff_region.exists("paralysed.png",0): 
                type(haste)
                wait(0.5)
            
            #verifies if it should engage combat while walking
            if label == "hunt" and lure_mode == 0: 
                slot1 = pixelColor(1130,500)
                if slot1 == "000000":
                    log("Mob detected on battle list while walking")
                    type(Key.ESC)
                    wait(0.5)
                    attack_function()
                    if running == 1: waypointer(label,wp)
                else: pass
                
            #in case shouldn't engane combat
            else: pass
        
        #if nothing changes on the screen for some time, add 1 to stopped timer
        if not minimap_region.somethingChanged:
            time_stopped+=1
            log("Walking "+str(time_stopped)+"/"+str(walk_interval)+" seconds")

        continue
    else: return

#function to verify if something is changing on screen
def changeHandler(event):
    event.region.somethingChanged = True
    event.region.stopObserver()

#wp_action list:
        #1: use rope
        #2: use ladder
        #3: use shovel

def waypoint_action(wp_action): 
    if wp_action == 1:
        type(rope)
        click(Location(screen_center_x,screen_center_y))
        log("Using rope")
        
    if wp_action == 2:
        click(Location(screen_center_x,screen_center_y))
        log("Using ladder")
        
    if wp_action == 3:
        type(shovel)
        click(Location(screen_center_x,screen_center_y))
        log("Using shovel")    
        
    wait(1)
    return

###############################################################################
   ###    ######## ########    ###     ######  ##    ## #### ##    ##  ######   
  ## ##      ##       ##      ## ##   ##    ## ##   ##   ##  ###   ## ##    ##  
 ##   ##     ##       ##     ##   ##  ##       ##  ##    ##  ####  ## ##        
##     ##    ##       ##    ##     ## ##       #####     ##  ## ## ## ##   #### 
#########    ##       ##    ######### ##       ##  ##    ##  ##  #### ##    ##  
##     ##    ##       ##    ##     ## ##    ## ##   ##   ##  ##   ### ##    ##  
##     ##    ##       ##    ##     ##  ######  ##    ## #### ##    ##  ######   
###############################################################################

def attack_function():

    type(Key.SPACE)
    wait(0.3)
    attacking()
    
    #img = capture(game_region)
    #shutil.move(img,os.path.join(r"/Users/GabrielMargonato/Downloads/SIKULI/DATASET/"+str(int(time.time()))+'.png'))
    
    #checks for new mob on screen
    slot1 = pixelColor(1130,500)
    if slot1 == "000000": attack_function()
    
    else:
        log("Battle list clear")
        if loot_type == 4: melee_looter()
        return
    
def attacking(): 
   
    battlelist_region.waitVanish("bl_target.png",30) #waits for 30 seconds before switching mob
    
    #after mob is dead:
    
    if loot_type == 1: 
        melee_looter()
        if message_region.exists("valuable_loot.png",0): 
            log("[ATTENTION] Valuable loot dropped")
            melee_looter()
        
    elif loot_type == 2 and message_region.exists("valuable_loot.png",0):
        log("[ATTENTION] Valuable loot dropped")
        melee_looter()
        melee_looter()

    elif loot_type == 3: 
        try:target_loot()
        except: pass

    else: return

#################################################################
##        #######   #######  ######## ######## ######## ########  
##       ##     ## ##     ##    ##       ##    ##       ##     ## 
##       ##     ## ##     ##    ##       ##    ##       ##     ## 
##       ##     ## ##     ##    ##       ##    ######   ########  
##       ##     ## ##     ##    ##       ##    ##       ##   ##   
##       ##     ## ##     ##    ##       ##    ##       ##    ##  
########  #######   #######     ##       ##    ######## ##     ## 
#################################################################

#loot_type = 0 -> ignore loot
#loot_type = 1 -> loot everything
#loot_type = 2 -> loot only valuable
#loot_type = 3 -> identy a corpse from loot_corpses list inside game_region
#loot_type = 4 -> loot only after clearing the battle list (best used with lure_mode)

def melee_looter():
    log("Looting around char")
    click(Location(430,265),8) #1
    click(Location(462,265),8) #2
    click(Location(495,265),8) #3
    click(Location(495,297),8) #4   
    click(Location(495,330),8) #5
    click(Location(462,330),8) #6
    click(Location(430,330),8) #7    
    click(Location(430,297),8) #8
    click(Location(screen_center_x,screen_center_y),8) #9

def target_loot():
    wait(1)
    corpses_on_screen = findAnyList(loot_corpses)
    number_of_corpses_found = len(corpses_on_screen)
    str_corpses_location = str(corpses_on_screen)[1:-1]
    log(str(number_of_corpses_found)+" corpse(s) found on screen")
    for corpse in corpses_on_screen:
        log("Looting corpse at "+str(corpse.getX())+","+str(corpse.getY()))
        click(corpse,8)
        hover(Location(screen_center_x,screen_center_y))
        last_loot_region = Region(3,760,173,18)
        last_loot_region.waitVanish("loot_msg.png",3)
        break

#######################################################
##     ##  #######  ######## ##    ## ######## ##    ## 
##     ## ##     ##    ##    ##   ##  ##        ##  ##  
##     ## ##     ##    ##    ##  ##   ##         ####   
######### ##     ##    ##    #####    ######      ##    
##     ## ##     ##    ##    ##  ##   ##          ##    
##     ## ##     ##    ##    ##   ##  ##          ##    
##     ##  #######     ##    ##    ## ########    ##    
#######################################################

#function to prevent being exhausted
def sendHotkey(actionList):
    
    #                0        1       2       3
    #actionList = ["name","hotkey","group",cooldown]
    
    global lastHeal
    global lastObj
    global lastSupp

    now = datetime.now()
               
    if actionList[2] == "heal":
    
        diff = (now - lastHeal).total_seconds()
        if diff >= actionList[3]:
            log("Casting heal spell \'"+actionList[0]+"\'")
            type(actionList[1])        
            lastHeal = datetime.now()

    elif actionList[2] == "object":
    
        diff = (now - lastObj).total_seconds()
        if diff >= actionList[3]:
            log("Using item \'"+actionList[0]+"\'")
            type(actionList[1])        
            lastObj = datetime.now()
        
    #                0        1       2       3        4
    #actionList = ["name","hotkey","group",cooldown,last_cast]
    elif actionList[2] == "atk":
    
        diff = (now - actionList[4]).total_seconds()
        if diff >= actionList[3]:
            log("Casting attack spell \'"+actionList[0]+"\'")    
            type(actionList[1])
            actionList[4] = datetime.now()
            sleep(2)
        else: return

    else: return
            
#############################################################
##     ## ########    ###    ##       #### ##    ##  ######   
##     ## ##         ## ##   ##        ##  ###   ## ##    ##  
##     ## ##        ##   ##  ##        ##  ####  ## ##        
######### ######   ##     ## ##        ##  ## ## ## ##   #### 
##     ## ##       ######### ##        ##  ##  #### ##    ##  
##     ## ##       ##     ## ##        ##  ##   ### ##    ##  
##     ## ######## ##     ## ######## #### ##    ##  ######   
#############################################################

#Healing
def healer_function(arg):
    while running == 1:

        if running == 0: break

        if vocation == 0:

            life = healerColor(15,55)
            if life == "bc8900" or life == "b01a20": 
                sendHotkey(light_heal) 
                if life == "b01a20":
                    img = capture(Screen().getBounds())
                    shutil.move(img,os.path.join(r"/Users/GabrielMargonato/Downloads/SIKULI/SESSIONS/"+str(session_id)+'_red_life.png'))
       
            sleep(1)
            continue
            
        else:

            life = healerColor(15,55)
            if life == "b01a20": 
                sendHotkey(intense_heal)
                sendHotkey(emergency_heal)  
                img = capture(Screen().getBounds())
                shutil.move(img,os.path.join(r"/Users/GabrielMargonato/Downloads/SIKULI/SESSIONS/"+str(session_id)+'_red_life.png'))
                continue
            
            mana = healerColor(660,71)
            if mana != "00266d": sendHotkey(mana_pot)  
            
            if life == "bc8900": sendHotkey(intense_heal)         
            if life == "5a9200": sendHotkey(light_heal)  

    else: print "Ending healer thread"

def startHealerThread():
    healer_thread = threading.Thread(target=healer_function, args = (0,))
    if healer_thread.isAlive() == False:
        print "Starting healer thread"
        healer_thread.start()
    else: 
        print "[ERROR] Healer thread already running"
    
################################################################################
########    ###    ########   ######   ######## ######## #### ##    ##  ######   
   ##      ## ##   ##     ## ##    ##  ##          ##     ##  ###   ## ##    ##  
   ##     ##   ##  ##     ## ##        ##          ##     ##  ####  ## ##        
   ##    ##     ## ########  ##   #### ######      ##     ##  ## ## ## ##   #### 
   ##    ######### ##   ##   ##    ##  ##          ##     ##  ##  #### ##    ##  
   ##    ##     ## ##    ##  ##    ##  ##          ##     ##  ##   ### ##    ##  
   ##    ##     ## ##     ##  ######   ########    ##    #### ##    ##  ######       
################################################################################

#Targeting Spell  
def spell_caster_function(arg):
    while running == 1:  
        if battlelist_region.exists("bl_target.png",0):            
            if use_exeta == 1: sendHotkey(exeta_res)
            if stay_diagonal == 1: near_targets("diagonal")

            #logic to cast atk spells
            for atk_spell in atk_spells: 

                #if its a box spell, call near_targets as mode = BOX
                spell_box_list = ["exori","exori gran"]    
                if atk_spell[0] in spell_box_list:
                    isBoxSpell = 1
                    green_light = near_targets("box")

                #if is not a box spell, but it is an spell that requeires mob alignment, call near_targets as mode = ALIGN
                elif atk_spell[0] == "exori min":
                    isBoxSpell = 1
                    green_light = near_targets("align")
                    
                else: isBoxSpell = 0
        
                if (isBoxSpell) == 0 or (isBoxSpell == 1 and green_light == 1): 
                   sendHotkey(atk_spell)
            
            if running == 0: break
        else: wait("bl_target.png",FOREVER)
    
    else: print "Ending spell caster thread"

def startSpellCasterThread():
    spell_cast_thread = threading.Thread(target=spell_caster_function, args = (0,))
    if spell_cast_thread.isAlive() == False:
        print "Starting spell caster thread"
        spell_cast_thread.start()
    else: 
        print "[ERROR] Spell caster thread already running"
    
#checks for targets around character
def near_targets(mode):

    #                    preto    verde  vd.claro  amarelo
    life_bar_colors = ["000000","0aba00","4eb949","b3b800"]

    #1 2 3
    #4 c 5
    #6 7 8

    x1 = 432 
    x2 = 463 
    x3 = 496
    
    y1 = 246
    y2 = 278
    y3 = 310
    
    pos1aux = (x1,y1)
    pos1 = pixelColor(pos1aux[0],pos1aux[1])
    
    pos2aux = (x2,y1)
    pos2 = pixelColor(pos2aux[0],pos2aux[1])

    pos3aux = (x3,y1)
    pos3 = pixelColor(pos3aux[0],pos3aux[1])
    
    pos4aux = (x1,y2)
    pos4 = pixelColor(pos4aux[0],pos4aux[1])
    
    pos5aux = (x3,y2)
    pos5 = pixelColor(pos5aux[0],pos5aux[1])
    
    pos6aux = (x1,y3)
    pos6 = pixelColor(pos6aux[0],pos6aux[1]) 
    
    pos7aux = (x2,y3)
    pos7 = pixelColor(pos7aux[0],pos7aux[1])
    
    pos8aux = (x3,y3)
    pos8 = pixelColor(pos8aux[0],pos8aux[1])
    
    ######################
    if mode == "box":

        #count number of targets around
        targets_around = 0
        if pos1 in life_bar_colors: targets_around += 1   
        if pos2 in life_bar_colors: targets_around += 1
        if pos3 in life_bar_colors: targets_around += 1
        if pos4 in life_bar_colors: targets_around += 1
        if pos5 in life_bar_colors: targets_around += 1                
        if pos6 in life_bar_colors: targets_around += 1        
        if pos7 in life_bar_colors: targets_around += 1       
        if pos8 in life_bar_colors: targets_around += 1
        
        if targets_around >= min_to_box:
            return 1
        else: return 0
        
    ######################
    if mode == "align":
        
        align_top = 0
        if pos1 in life_bar_colors: align_top += 1
        if pos2 in life_bar_colors: align_top += 1
        if pos3 in life_bar_colors: align_top += 1

        align_right = 0
        if pos3 in life_bar_colors: align_right += 1
        if pos5 in life_bar_colors: align_right += 1
        if pos8 in life_bar_colors: align_right += 1

        align_bottom = 0
        if pos6 in life_bar_colors: align_bottom += 1
        if pos7 in life_bar_colors: align_bottom += 1
        if pos8 in life_bar_colors: align_bottom += 1

        align_left = 0
        if pos1 in life_bar_colors: align_left += 1
        if pos4 in life_bar_colors: align_left += 1
        if pos6 in life_bar_colors: align_left += 1

        #optimal_align = max(align_top,align_right,align_bottom,align_left)
        #log("Optimal mob alignment: "+optimal_align)

        if align_top >= min_to_align: 
            type(Key.UP, KeyModifier.CMD)
            return 1

        elif align_right >= min_to_align:
            type(Key.RIGHT, KeyModifier.CMD)
            return 1
        
        elif align_bottom >= min_to_align:
            type(Key.DOWN, KeyModifier.CMD)
            return 1
                    
        elif align_left >= min_to_align:
            type(Key.LEFT, KeyModifier.CMD)
            return 1

        else: return 0

    ######################
    if mode == "diagonal":
        
        if (pos2 in life_bar_colors or pos7 in life_bar_colors): 
            walk = randint(1,2)
            if walk == 1: type(Key.LEFT)
            if walk == 2: type(Key.RIGHT)
            return 0
        
        elif (pos4 in life_bar_colors or pos5 in life_bar_colors): 
            walk = randint(1,2)
            if walk == 1: type(Key.UP)
            if walk == 2: type(Key.DOWN)
            return 0
        
        else: return 0

    #other modes
    else: return 0    

####################################################################
########  ########   #######  ########  ########  ######## ########  
##     ## ##     ## ##     ## ##     ## ##     ## ##       ##     ## 
##     ## ##     ## ##     ## ##     ## ##     ## ##       ##     ## 
##     ## ########  ##     ## ########  ########  ######   ########  
##     ## ##   ##   ##     ## ##        ##        ##       ##   ##   
##     ## ##    ##  ##     ## ##        ##        ##       ##    ##  
########  ##     ##  #######  ##        ##        ######## ##     ## 
####################################################################

def drop_item(sprite,name):
    if exists(sprite,0):
        imageCount = len(list([x for x in findAll(sprite)]))
        for i in range(imageCount):
            log("Dropping "+name+" "+str(i+1)+"/"+str(imageCount))
            dragDrop(sprite, Location(screen_center_x,screen_center_y))
            wait(0.5)
    else: return
    
#################################################################
########  ######## ########  ##     ## ######## ########  ######  
##     ## ##       ##     ## ##     ## ##       ##       ##    ## 
##     ## ##       ##     ## ##     ## ##       ##       ##       
##     ## ######   ########  ##     ## ######   ######    ######  
##     ## ##       ##     ## ##     ## ##       ##             ## 
##     ## ##       ##     ## ##     ## ##       ##       ##    ## 
########  ######## ########   #######  ##       ##        ######  
#################################################################

def debuff_check():
    log("Checking debuffs...")
    if action_bar_region.exists(Pattern("utura_spell.png").exact(),0) or action_bar_region.exists(Pattern("utura_gran_spell.png").exact(),0): type(utura)
    #while debuff_region.exists("paralysed.png",0): type(haste)
    #while debuff_region.exists("food.png",0): type(food)
    #while debuff_region.exists("poison.png",0): type(exana_pox)
    if (equip_ring == 1 and equip_region.exists("ring.png",0)): type(ring)
    if (equip_amulet == 1 and equip_region.exists("amulet.png",0)): type (amulet)
    else:return
    
#########################################################################
 ######  ######## ##       ########  ######  ########  #######  ########  
##    ## ##       ##       ##       ##    ##    ##    ##     ## ##     ## 
##       ##       ##       ##       ##          ##    ##     ## ##     ## 
 ######  ######   ##       ######   ##          ##    ##     ## ########  
      ## ##       ##       ##       ##          ##    ##     ## ##   ##   
##    ## ##       ##       ##       ##    ##    ##    ##     ## ##    ##  
 ######  ######## ######## ########  ######     ##     #######  ##     ##
#########################################################################
    
def script_selector_function():
    script_list = (
            "-nothing selected-",
            "Rook Mino Hell",
            "Rook PSC",
            "Ab Wasp Cave",
            "Venore Amazon Camp",
            "Edron Earth Cave",
            "Darashia Dragons",
            "Formorgar Mines Cults",
            "Krailos Bug Cave -1",
            "Laguna Island",
            "Sea Serpent North",
            "Yalahar Mutated Tigers",
            "Nibelor Crystal Spiders",
            "Carlin Cults -1"
            
    )
    prompt = select("Please select a script from the list","Available Scripts", options = script_list, default = script_list[0])

    global selected_script
    
    if   prompt == script_list[1]: selected_script = "mino_hell" 
    elif prompt == script_list[2]: selected_script = "rook_psc"
    elif prompt == script_list[3]: selected_script = "ab_wasp"
    elif prompt == script_list[4]: selected_script = "amazon_camp"
    elif prompt == script_list[5]: selected_script = "bog_raider_edron"
    elif prompt == script_list[6]: selected_script = "darashia_dragons"
    elif prompt == script_list[7]: selected_script = "formorgar_cults"
    elif prompt == script_list[8]: selected_script = "krailos_bug_cave"
    elif prompt == script_list[9]: selected_script = "laguna_island"
    elif prompt == script_list[10]: selected_script = "sea_serpent_n"
    elif prompt == script_list[11]: selected_script = "ylr_mut_tiger"
    elif prompt == script_list[12]: selected_script = "ice_golem"
    elif prompt == script_list[13]: selected_script = "carlin_cults"
    else:
        popup("The selected script is not valid, terminating execution")
        closeFrame(0)
        raise Exception("Invalid Script")
       
    log("Selected Script: "+selected_script)

    #declare global variables
    global imported_script
    
    global vocation      
    global loot_type     
    global lure_mode  
    global use_exeta
    global equip_ring    
    global equip_amulet  
    global drop_vials    
    global stay_diagonal 
    global take_distance 
    
    global utura
    global light_heal    
    global intense_heal  
    global emergency_heal
    global mana_pot   
    
    global atk_spells
    
    global minimap_zoom
    global last_hunt_wp
    global last_leave_wp
    global last_go_hunt_wp
    
    #imports the script that will be executed on this session
    imported_script = importlib.import_module(selected_script)
    
    #set variables
    vocation      = imported_script.vocation
    loot_type     = imported_script.loot_type

    if loot_type == 3: 
        global loot_corpses
        loot_corpses = imported_script.loot_corpses
                                                            
    lure_mode     = imported_script.lure_mode
    use_exeta     = imported_script.use_exeta
    equip_ring    = imported_script.equip_ring
    equip_amulet  = imported_script.equip_amulet
    drop_vials    = imported_script.drop_vials
    stay_diagonal = imported_script.stay_diagonal
    take_distance = imported_script.take_distance

    #heal
    light_heal     = imported_script.light_heal
    intense_heal   = imported_script.intense_heal
    emergency_heal = imported_script.emergency_heal
    mana_pot       = imported_script.mana_pot
    
    #atk
    atk_spells = imported_script.atk_spells

    minimap_zoom    = imported_script.minimap_zoom
    last_hunt_wp    = imported_script.last_hunt_wp
    last_leave_wp   = imported_script.last_leave_wp
    last_go_hunt_wp = imported_script.last_go_hunt_wp
    
###############################################
######## ########     ###    ##     ## ######## 
##       ##     ##   ## ##   ###   ### ##       
##       ##     ##  ##   ##  #### #### ##       
######   ########  ##     ## ## ### ## ######   
##       ##   ##   ######### ##     ## ##       
##       ##    ##  ##     ## ##     ## ##       
##       ##     ## ##     ## ##     ## ######## 
###############################################

#receives a message and print it onto jframe
def log(message):
    textArea.append(str(datetime.now().strftime("%H:%M:%S.%f")[:-4])+" - "+str(message)+"\n")
    textArea.setCaretPosition(textArea.getDocument().getLength())

def closeFrame(event):
    global running
    running = 0
    frame.dispose()

frame = JFrame("AppleBot - Console Log")
frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE)
frame.setBounds(8,545,600,70)
contentPane = JPanel()
frame.setContentPane(contentPane)

buttonS = JButton("STOP", actionPerformed = closeFrame)
buttonS.setForeground(Color.RED)
frame.add(buttonS,WEST)

textArea = JTextArea(6,38)
#textArea.setFont(textArea.getFont().deriveFont(textArea.getFont().getSize() - 2.5))
textArea.setEditable(False)
contentPane.add(textArea)
scrollPane = JScrollPane(textArea, JScrollPane.VERTICAL_SCROLLBAR_ALWAYS, JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED)
contentPane.add(scrollPane)
frame.setUndecorated(True)
frame.setAlwaysOnTop(True)
frame.pack()
frame.setVisible(True)
log("Initializing bot")

##############################################
 ######  ########    ###    ########  ######## 
##    ##    ##      ## ##   ##     ##    ##    
##          ##     ##   ##  ##     ##    ##    
 ######     ##    ##     ## ########     ##    
      ##    ##    ######### ##   ##      ##    
##    ##    ##    ##     ## ##    ##     ##    
 ######     ##    ##     ## ##     ##    ##    
##############################################

#generates an ID for this session
session_id = str(datetime.now().strftime("%d%m%Y%H%M"))
log("Session ID: "+str(session_id))

#calls script selector
script_selector_function()

#starting label
label = select("Please select a starting point","Available Starting Points", options = ("go_hunt","hunt","leave"), default = "go_hunt")

#starting waypoint number
if label == "go_hunt":
    available_wps = list(range(1,last_go_hunt_wp+1))
    
if label == "hunt":
    available_wps = list(range(1,last_hunt_wp+1))

if label == "leave":
    available_wps = list(range(1,last_leave_wp+1))

list_of_wps = map(str, available_wps)
wp_str = select("Choose a starting waypoint",label, list_of_wps, default = 0)
wp = int(wp_str)

log("Starting at "+label+" waypoint "+str(wp))
log("[ATTENTION] Walk interval is set to "+str(walk_interval)+" seconds")


#If game client exists, focus on it. Else, throws exception
if(App("Tibia").isRunning() == True): App.focus("Tibia")
else:
    frame.dispose()
    raise Exception('Tibia client not running.')

#shows ping on game screen
if not exists(Pattern("ping.png").similar(0.50),0): type(Key.F8, KeyModifier.ALT)

#adjusts the starting minimap zoom for this session
def adjust_minimap_zoom():
    #subtract zoom
    for i in range(0,3):
        click(Location(1240,246))
    
    #add zoom
    for i in range(0,minimap_zoom):
        click(Location(1240,227))

log("Adjusting minimap zoom to "+str(minimap_zoom))
adjust_minimap_zoom()

#sets session channel
if loot_type >= 1: click("loot_channel.png")
else: click("server_log_channel.png")

#last cast time for heals, objects and spells alike
lastObj  = datetime.now()
lastHeal = datetime.now()   
exeta_res.append(datetime.now())
for atk_spell in atk_spells:
    atk_spell.append(datetime.now())

#start threads
running = 1
startHealerThread()
if vocation > 0: startSpellCasterThread()


###########################################################################
##     ##    ###    #### ##    ##    ##        #######   #######  ########  
###   ###   ## ##    ##  ###   ##    ##       ##     ## ##     ## ##     ## 
#### ####  ##   ##   ##  ####  ##    ##       ##     ## ##     ## ##     ## 
## ### ## ##     ##  ##  ## ## ##    ##       ##     ## ##     ## ########  
##     ## #########  ##  ##  ####    ##       ##     ## ##     ## ##        
##     ## ##     ##  ##  ##   ###    ##       ##     ## ##     ## ##        
##     ## ##     ## #### ##    ##    ########  #######   #######  ##        
###########################################################################

#Main
while running == 1:
 
    if label == "hunt": 
        slot1 = pixelColor(1130,500)
        if slot1 == "000000": 
            log("Mob detected on battle list")
            attack_function()
        if vocation > 0: debuff_check()

    if running == 0: closeFrame(0);break
    
    try: 
        wp_action = waypointer(label,wp)
        #verifies if should perform some action when reaches destination
        if wp_action > 0: waypoint_action(wp_action)
            
        #After arriving at destination waypoint
        log("Arrived at "+label+" waypoint "+str(wp))
        
        #########################################
        #current waypoint is the last one for hunt
        if (label == "hunt" and wp >= last_hunt_wp):

            #check if should drop vials
            if drop_vials == 1: 
                log("Searching for vials to drop...")
                drop_item(Pattern("small_flask.png").exact(),"small empty flask")
                drop_item(Pattern("strong_flask.png").exact(),"strong empty flask")
                drop_item(Pattern("great_flask.png").exact(),"great empty flask")
            
            #check if it should leave the hunt
            log("Checking exit hunt conditions...")
            label = imported_script.exit_conditions()

            #reset waypoint back to 1
            wp = 1
               
            #prints the screen after a sucessfull run and saves it
            log("Printing session ID "+str(session_id)) 
            img = capture(Screen().getBounds())
            shutil.move(img,os.path.join(r"/Users/GabrielMargonato/Downloads/SIKULI/SESSIONS/"+session_id+'.png'))
    
        ##########################################
        #current waypoint is the last one for leave
        elif label == "leave" and wp >= last_leave_wp:
            logoff_function()
            
        ##########################################
        #current waypoint is the last one for go_hunt
        elif label == "go_hunt" and wp >= last_go_hunt_wp:
            log("Setting label to Hunt")
            label = "hunt"
            wp = 1
            
        ##########################################
        #no criterea matched
        else: 
            wp+=1
    except:
        log("[ERROR] waypoint "+label+" "+str(wp)+" not found!")
        #move to next waypoint
        if   label == "go_hunt" and wp > last_go_hunt_wp:
            adjust_minimap_zoom()
            wp = 1
        elif label == "hunt"    and wp > last_hunt_wp: 
            adjust_minimap_zoom()
            wp = 1
        elif label == "leave"   and wp > last_leave_wp: 
            adjust_minimap_zoom()
            wp = 1
        else: wp+=1

else: popup("END")
#end
