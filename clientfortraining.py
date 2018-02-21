#!/usr/bin/python
import sys
import math
import snakeoil
import numpy as np
import csv
target_speed= 0 
lap= 0 
prev_distance_from_start= 1 
learn_final= False 
opHistory= list() 
trackHistory= [0] 
TRACKHISTORYMAX= 50 
secType= 0 
secBegin= 0 
secMagnitude= 0 
secWidth= 0 
sangs= [-45,-19,-12,-7,-4,-2.5,-1.7,-1,-.5,0,.5,1,1.7,2.5,4,7,12,19,45]
sangsrad= [(math.pi*X/180.0) for X in sangs]
badness= 0
class Track():
    def __init__(self):
        self.laplength= 0 
        self.width= 0 
        self.sectionList= list() 
        self.usable_model= False 
    def __repr__(self):
        o= 'TrackList:\n'
        o+= '\n'.join([repr(x) for x in self.sectionList])
        o+= "\nLap Length: %s\n" % self.laplength
        return o
    def post_process_track(self):
        ws= [round(s.width) for s in self.sectionList]
        ws= filter(lambda O:O,ws) 
        ws.sort()          
        self.width= ws[len(ws)/2]   
        cleanedlist= list()
        TooShortToBeASect= 6
        for n,s in enumerate(self.sectionList):
            if s.dist > TooShortToBeASect:  
                if cleanedlist and not s.direction and not cleanedlist[-1].direction:
                    cleanedlist[-1].end= s.end
                else:
                    cleanedlist.append(s)
            else:
                if cleanedlist: 
                    prevS= cleanedlist[-1] 
                    prevS.end= s.apex 
                    prevS.dist= prevS.end-prevS.start
                    prevS.apex= prevS.dist/2 + prevS.start
                if len(self.sectionList)-1 >= n+1: 
                    nextS= self.sectionList[n+1]
                    nextS.start= s.apex 
                    nextS.dist= nextS.end-nextS.start  
                    nextS.apex= nextS.dist/2 + nextS.start
                else: 
                    prevS.end= T.laplength  
                    prevS.dist= prevS.end-prevS.start
                    prevS.apex= prevS.dist/2 + prevS.start
        self.sectionList= cleanedlist
        self.usable_model= True 
    def write_track(self,fn):
        firstline= "%f\n" % self.width 
        f= open(fn+'.trackinfo','w')
        f.write(firstline)
        for s in self.sectionList:
            ts= '%f %f %f %d\n' % (s.start,s.end,s.magnitude,s.badness)
            f.write(ts)
        f.close()
    def load_track(self,fn):
        self.sectionList= list() 
        with open(fn+'.trackinfo','r') as f:
            self.width= float(f.readline().strip())
            for l in f:
                data=l.strip().split(' ') 
                TS= TrackSection(float(data[0]),float(data[1]),float(data[2]),self.width,int(data[3]))
                self.sectionList.append(TS)
        self.laplength= self.sectionList[-1].end
        self.usable_model= True 
    def section_in_now(self,d):
        for s in self.sectionList:
            if s.start < d < s.end:
                return s
        else:
            return None
    def section_ahead(self,d):
        for n,s in enumerate(self.sectionList):
            if s.start < d < s.end:
                if n < len(self.sectionList)-1:
                    return self.sectionList[n+1]
                else: 
                    return self.sectionList[0]
        else:
            return None
    def record_badness(self,b,d):
        sn= self.section_in_now(d)
        if sn:
            sn.badness+= b
class TrackSection():
    def __init__(self,sBegin,sEnd,sMag,sWidth,sBadness):
        if sMag:
            self.direction= int(abs(sMag)/sMag) 
        else:
            self.direction= 0 
        self.start= sBegin 
        self.end= sEnd     
        self.dist= self.end-self.start
        if not self.dist: self.dist= .1 
        self.apex= self.start + self.dist/2 
        self.magnitude= sMag 
        self.width= sWidth 
        self.severity= self.magnitude/self.dist 
        self.badness= sBadness
    def __repr__(self):
        tt= ['Right', 'Straight', 'Left'][self.direction+1]
        o=  "S: %f  " % self.start
        o+= "E: %f  " % self.end
        o+= "L: %f  " % (self.end-self.start)
        o+= "Type: %s  " % tt
        o+= "M: %f " % self.magnitude
        o+= "B: %f " % self.badness
        return o
    def update(self, distFromStart, trackPos, steer, angle, z):
        pass
    def current_section(self,x):
        return self.begin <= x and x <= self.end
def automatic_transimission(P,r,g,c,rpm,sx,ts,tick):
    clutch_releaseF= .05 
    ng,nc= g,c 
    if ts < 0 and g > -1: 
        ng= -1
        nc= 1
    elif ts>0 and g<0:
        ng= g+1
        nc= 1
    elif c > 0:
        if g: 
            nc= c - clutch_releaseF 
        else: 
            if ts < 0:
                ng= -1 
            else:
                ng= 1 
    elif not tick % 50 and sx > 20:
        pass 
    elif g==6 and rpm<P['dnsh5rpm']: 
        ng= g-1 
        nc= 1
    elif g==5 and rpm<P['dnsh4rpm']: 
        ng= g-1 
        nc= 1
    elif g==4 and rpm<P['dnsh3rpm']:
        ng= g-1 
        nc= 1
    elif g==3 and rpm<P['dnsh2rpm']:
        ng= g-1 
        nc= 1
    elif g==2 and rpm<P['dnsh1rpm']:
        ng= g-1 
        nc= 1
    elif g==5 and rpm>P['upsh6rpm']: 
        ng= g+1
        nc= 1
    elif g==4 and rpm>P['upsh5rpm']: 
        ng= g+1
        nc= 1
    elif g==3 and rpm>P['upsh4rpm']: 
        ng= g+1
        nc= 1
    elif g==2 and rpm>P['upsh3rpm']: 
        ng= g+1
        nc= 1
    elif g==1 and rpm>P['upsh2rpm']: 
        ng= g+1
        nc= 1
    elif not g:
        ng= 1
        nc= 1
    else:
        pass
    return ng,nc
def find_slip(wsv_list):
    w1,w2,w3,w4= wsv_list
    if w1:
        slip= (w3+w4) - (w1+w2)
    else:
        slip= 0
    return slip
def track_sensor_analysis(t,a):
    alpha= 0
    sense= 1 
    farthest= None,None 
    ps= list()
    realt= list()
    sangsradang= [(math.pi*X/180.0)+a for X in sangs] 
    for n,sang in enumerate(sangsradang):
        x,y= t[n]*math.cos(sang),t[n]*-math.sin(sang)
        if float(x) > 190:
            alpha= math.pi
        else:
            ps.append((x,y))
            realt.append(t[n])
    firstYs= [ p[1] for p in ps[0:3] ]
    lastYs= [ p[1] for p in ps[-3:] ]
    straightnessf= abs(1- abs(min(firstYs))/max(.0001,abs(max(firstYs))))
    straightnessl= abs(1- abs(min(lastYs))/max(.0001,abs(max(lastYs))))
    straightness= max(straightnessl,straightnessf)
    farthest= realt.index(max(realt))
    ls= ps[0:farthest] 
    rs= ps[farthest+1:] 
    rs.reverse() 
    if farthest > 0 and farthest < len(ps)-1: 
        beforePdist= t[farthest-1]
        afterPdist=  t[farthest+1]
        if beforePdist > afterPdist: 
            sense= -1
            outsideset= ls
            insideset= rs
            ls.append(ps[farthest]) 
        else:                        
            outsideset= rs
            insideset= ls
            rs.append(ps[farthest]) 
    else: 
        if ps[0][0] > ps[-1][0]: 
            ps.reverse()
            farthest= (len(ps)-1) - farthest 
        if ps[0][1] > ps[-1][1]: 
            sense= -1
            outsideset= ls
            insideset= rs
        else: 
            outsideset= rs
            insideset= ls
    maxpdist= 0
    if not outsideset:
        return (0,a,2)
    nearx,neary= outsideset[0][0],outsideset[0][1]
    farx,fary= outsideset[-1][0],outsideset[-1][1]
    cdeltax,cdeltay= (farx-nearx),(fary-neary)
    c= math.sqrt(cdeltax*cdeltax + cdeltay*cdeltay)
    for p in outsideset[1:-1]: 
        dx1= p[0] - nearx
        dy1= p[1] - neary
        dx2= p[0] - farx
        dy2= p[1] - fary
        a= math.sqrt(dx1*dx1+dy1*dy1)
        b= math.sqrt(dx2*dx2+dy2*dy2)
        pdistances= a + b
        if pdistances > maxpdist:
            maxpdist= pdistances
            inflectionp= p  
            ia= a 
            ib= b 
    if maxpdist and not alpha:
        infleX= inflectionp[0]
        preprealpha= 2*ia*ib
        if not preprealpha: preprealpha= .00000001 
        prealpha= (ia*ia+ib*ib-c*c)/preprealpha
        if prealpha > 1: alpha= 0
        elif prealpha < -1: alpha= math.pi
        else:
            alpha= math.acos(prealpha)
        turnsangle= sense*(180-(alpha *180 / math.pi))
    else:
        infleX= max(t)
        turnsangle= sangs[t.index(infleX)]
    return (infleX,turnsangle,straightness)
def speed_planning(P,d,t,tp,sx,sy,st,a,infleX,infleA):
    cansee= max(t[2:17])
    if cansee > 0:
        carmax= P['carmaxvisib'] * cansee 
    else:
        carmax= 69
    if cansee <0: 
        return P['backontracksx'] 
    if cansee > 190 and abs(a)<.1:
        return carmax 
    if t[9] < 40: 
        return P['obviousbase'] + t[9] * P['obvious']
    if infleA:
        willneedtobegoing= 600-180.0*math.log(abs(infleA))
        willneedtobegoing= max(willneedtobegoing,P['carmin']) 
    else: 
        willneedtobegoing= carmax
    brakingpacecut= 150 
    if sx > brakingpacecut:
        brakingpace= P['brakingpacefast']
    else:
        brakingpace= P['brakingpaceslow']
    base= min(infleX * brakingpace + willneedtobegoing,carmax)
    base= max(base,P['carmin']) 
    if st<P['consideredstr8']: 
        return base
    uncoolsy= abs(sy)/sx
    syadjust= 2 - 1 / P['oksyp'] * uncoolsy
    return base * syadjust 
def damage_speed_adjustment(d):
    dsa= 1
    if d > 1000: dsa=.98
    if d > 2000: dsa=.96
    if d > 3000: dsa=.94
    if d > 4000: dsa=.92
    if d > 5000: dsa=.90
    if d > 6000: dsa=.88
    return dsa
def jump_speed_adjustment(z):
    offtheground= snakeoil.clip(z-.350,0,1000)
    jsa= offtheground * -800
    return jsa
def traffic_speed_adjustment(os,sx,ts,tsen):
    global opHistory
    if not opHistory: 
        opHistory= os 
        return 0 
    tsa= 0 
    mpn= 0 
    sn=  min(os[17],os[18])  
    if sn > tsen[9] and tsen[9]>0: 
        return 0                   
    if sn < 15:
        sn=  min(sn , os[16],os[19])  
    if sn < 8:
        sn=  min(sn , os[15],os[20])  
    sn-= 5 
    if sn<3: 
        opHistory= os 
        return -ts 
    opn= mpn+sn 
    mpp= mpn - sx/180 
    sp= min(opHistory[17],opHistory[18]) 
    if sp < 15:
        sp=  min(sp , os[16],os[19])  
    if sp < 8:
        sp=  min(sn , os[15],os[20])  
    sp-= 5 
    opHistory= os 
    opp= mpp+sp 
    osx= (opn-opp) * 180 
    osx= snakeoil.clip(osx,0,300) 
    if osx-sx > 0: return 0 
    max_tsa= osx - ts 
    max_worry= 80 
    full_serious= 20 
    if sn > max_worry:
        seriousness= 0
    elif sn < full_serious:
        seriousness= 1
    else:
        seriousness= (max_worry-sn)/(max_worry-full_serious)
    tsa= max_tsa * seriousness
    tsa= snakeoil.clip(tsa,-ts,0) 
    return tsa
def steer_centeralign(P,sti,tp,a,ttp=0):
    pointing_ahead= abs(a) < P['pointingahead'] 
    onthetrack= abs(tp) < P['sortofontrack']
    offrd= 1
    if not onthetrack:
        offrd= P['offroad']
    if pointing_ahead:
        sto= a 
    else:
        sto= a * P['backward']
    ttp*= 1-a  
    sto+= (ttp - min(tp,P['steer2edge'])) * P['s2cen'] * offrd 
    return sto 
def speed_appropriate_steer(P,sto,sx):
    if sx > 0:
        stmax=  max(P['sxappropriatest1']/math.sqrt(sx)-P['sxappropriatest2'],P['safeatanyspeed'])
    else:
        stmax= 1
    return snakeoil.clip(sto,-stmax,stmax)
def steer_reactive(P,sti,tp,a,t,sx,infleX,infleA,str8ness):
    if abs(a) > .6: 
        return steer_centeralign(P,sti,tp,a)
    maxsen= max(t)
    ttp= 0
    aadj= a
    if maxsen > 0 and abs(tp) < .99:
        MaxSensorPos= t.index(maxsen)
        MaxSensorAng= sangsrad[MaxSensorPos]
        sensangF= -.9  
        aadj= MaxSensorAng * sensangF
        if maxsen < 40:
            ttp= MaxSensorAng * - P['s2sen'] / maxsen
        else: 
            if str8ness < P['str8thresh'] and abs(infleA)>P['ignoreinfleA']:
                ttp= -abs(infleA)/infleA
                aadj= 0 
            else:
                ttp= 0
        senslimF= .031 
        ttp= snakeoil.clip(ttp,tp-senslimF,tp+senslimF)
    else: 
        aadj= a
        if tp:
            ttp= .94 * abs(tp) / tp
        else:
            ttp= 0
    sto= steer_centeralign(P,sti,tp,aadj,ttp)
    return speed_appropriate_steer(P,sto,sx)
def traffic_navigation(os, sti):
    sto= sti 
    c= min(os[4:32]) 
    cs= os.index(c)  
    if not c: c= .0001
    if min(os[18:26])<7:
        sto+= .5/c
    if min(os[8:17])<7:
        sto-= .5/c
    if cs == 17:
        sto+= .1/c
    if cs == 18:
        sto-= .1/c
    if .1 < os[17] < 40:
        sto+= .01
    if .1 < os[18] < 40:
        sto-= .01
    return sto
def clutch_control(P,cli,sl,sx,sy,g):
    if abs(sx) < .1 and not cli: 
        return 1  
    clo= cli-.2 
    clo+= sl/P['clutchslip']
    clo+= sy/P['clutchspin']
    return clo
def throttle_control(P,ai,ts,sx,sl,sy,ang,steer):
    ao= ai 
    if ts < 0:
        tooslow= sx-ts 
    else:
        okmaxspeed4steer= P['stst']*steer*steer-P['st']*steer+P['stC']
        if steer> P['fullstis']:
            ts=P['fullstmaxsx']
        else:
            ts= min(ts,okmaxspeed4steer)
        tooslow= ts-sx 
    ao= 2 / (1+math.exp(-tooslow)) -1
    ao-= abs(sl) * P['slipdec'] 
    spincut= P['spincutint']-P['spincutslp']*abs(sy)
    spincut= snakeoil.clip(spincut,P['spincutclip'],1)
    ao*= spincut
    ww= abs(ang)/P['wwlim']
    wwcut=  min(ww,.1)
    if ts>0 and sx >5:
        ao-= wwcut
    if ao > .8: ao= 1
    return ao
def brake_control(P,bi,sx,sy,ts,sk):
    bo= bi 
    toofast= sx-ts
    if toofast < 0: 
        return 0
    if toofast: 
        bo+= P['brake'] * toofast / max(1,abs(sk))
        bo=1
    if sk > P['seriousABS']: bo=0 
    if sx < 0: bo= 0 
    if sx < -.1 and ts > 0:  
        bo+= .05
    sycon= 1
    if sy:
        sycon= min(1,  P['sycon2']-P['sycon1']*math.log(abs(sy))  )
    return min(bo,sycon)
def iberian_skid(wsv,sx):
    speedps= sx/3.6
    sxshouldbe= sum( [ [.3179,.3179,.3276,.3276][x] * wsv[x] for x in range(3) ] ) / 4.0
    return speedps-sxshouldbe
def skid_severity(P,wsv_list,sx):
    skid= 0
    avgws= sum(wsv_list)/4 
    if avgws:
        skid= P['skidsev1']*sx/avgws - P['wheeldia'] 
    return skid
def car_might_be_stuck(sx,a,p):
    if p > 1.2 and a < -.5:
        return True
    if p < -1.2 and a > .5:
        return True
    if sx < 3: 
        return True
    return False 
def car_is_stuck(sx,t,a,p,fwdtsen,ts):
    if fwdtsen > 5 and ts > 0: 
        return False
    if abs(a)<.5 and abs(p)<2 and ts > 0: 
        return False
    if t < 100: 
        return False
    return True
def learn_track(st,a,t,dfs):
    global secType
    global secBegin
    global secMagnitude
    global secWidth
    NOSTEER= 0.07 
    T.laplength= max(dfs,T.laplength)
    if len(trackHistory) >= TRACKHISTORYMAX:
        trackHistory.pop(0) 
    trackHistory.append(st)
    steer_sma= sum(trackHistory)/len(trackHistory) 
    if abs(steer_sma) > NOSTEER: 
        secType_now= abs(steer_sma)/steer_sma
        if secType != secType_now: 
            T.sectionList.append( TrackSection(secBegin,dfs, secMagnitude, secWidth,0) )
            secMagnitude= 0 
            secWidth= 0 
            secType= secType_now 
            secBegin= dfs 
        secMagnitude+= st 
    else: 
        if secType: 
            T.sectionList.append( TrackSection(secBegin,dfs, secMagnitude, secWidth,0) )
            secMagnitude= 0 
            secWidth= 0 
            secType= 0 
            secBegin= dfs 
    if not secWidth and abs(a) < NOSTEER:
        secWidth= t[0]+t[-1] 
def learn_track_final(dfs):
    global secType
    global secBegin
    global secMagnitude
    global secWidth
    global badness
    T.sectionList.append( TrackSection(secBegin,dfs, secMagnitude, secWidth, badness) )
def drive(c,tick):
    S,R,P= c.S.d,c.R.d,c.P
    global target_speed
    global lap
    global prev_distance_from_start
    global learn_final
    global badness
    badness= S['damage']-badness 
    skid= skid_severity(P,S['wheelSpinVel'],S['speedX'])
    if skid>1:
        badness+= 15
    if car_might_be_stuck(S['speedX'],S['angle'],S['trackPos']):
        S['stucktimer']= (S['stucktimer']%400) + 1
        if car_is_stuck(S['speedX'],S['stucktimer'],S['angle'],
                        S['trackPos'],S['track'][9],target_speed):
            badness+= 100
            R['brake']= 0 
            if target_speed > 0:
                target_speed= -40
            else:
                target_speed= 40
    else: 
        S['stucktimer']= 0
    if S['z']>4: 
        badness+= 20
    infleX,infleA,straightness= track_sensor_analysis(S['track'],S['angle'])
    if target_speed>0:
        if c.stage: 
            if not S['stucktimer']:
                target_speed= speed_planning(P,S['distFromStart'],S['track'],S['trackPos'],
                                          S['speedX'],S['speedY'],R['steer'],S['angle'],
                                          infleX,infleA)
            target_speed+= jump_speed_adjustment(S['z'])
            if c.stage > 1: 
                target_speed+= traffic_speed_adjustment(
                          S['opponents'],S['speedX'],target_speed,S['track'])
            target_speed*= damage_speed_adjustment(S['damage'])
        else:
            if lap > 1 and T.usable_model:
                target_speed= speed_planning(P,S['distFromStart'],S['track'],S['trackPos'],
                                           S['speedX'],S['speedY'],R['steer'],S['angle'],
                                          infleX,infleA)
                target_speed*= damage_speed_adjustment(S['damage'])
            else: 
                target_speed= 50
    target_speed= min(target_speed,333)
    caution= 1 
    if T.usable_model:
        snow= T.section_in_now(S['distFromStart'])
        snext= T.section_ahead(S['distFromStart'])
        if snow:
            if snow.badness>100: caution= .80
            if snow.badness>1000: caution= .65
            if snow.badness>10000: caution= .4
            if snext:
                if snow.end - S['distFromStart'] < 200: 
                    if snext.badness>100: caution= .90
                    if snext.badness>1000: caution= .75
                    if snext.badness>10000: caution= .5
    target_speed*= caution
    if T.usable_model or c.stage>1:
        if abs(S['trackPos']) > 1:
            s= steer_centeralign(P,R['steer'],S['trackPos'],S['angle'])
            badness+= 1
        else:
            s= steer_reactive(P,R['steer'],S['trackPos'],S['angle'],S['track'],
                                                   S['speedX'],infleX,infleA,straightness)
    else:
        s= steer_centeralign(P,R['steer'],S['trackPos'],S['angle'])
    R['steer']= s
    if S['stucktimer'] and S['distRaced']>20:
        if target_speed<0:
            R['steer']= -S['angle']
    if c.stage > 1: 
        if target_speed < 0: 
            target_speed*= snakeoil.clip(S['opponents'][0]/20,  .1, 1)
            target_speed*= snakeoil.clip(S['opponents'][35]/20, .1, 1)
        else:
            R['steer']= speed_appropriate_steer(P,
                    traffic_navigation(S['opponents'], R['steer']),
                    S['speedX']+50)
    if not S['stucktimer']:
        target_speed= abs(target_speed) 
    slip= find_slip(S['wheelSpinVel'])
    R['accel']= throttle_control(P,R['accel'],target_speed,S['speedX'],slip,
                                 S['speedY'],S['angle'],R['steer'])
    if R['accel'] < .01:
        R['brake']= brake_control(P,R['brake'],S['speedX'],S['speedY'],target_speed,skid)
    else:
        R['brake']= 0
    R['gear'],R['clutch']= automatic_transimission(P,
           S['rpm'],S['gear'],R['clutch'],S['rpm'],S['speedX'],target_speed,tick)
    R['clutch']= clutch_control(P,R['clutch'],slip,S['speedX'],S['speedY'],S['gear'])
    if S['distRaced'] < S['distFromStart']: 
        lap= 0
    if prev_distance_from_start > S['distFromStart'] and abs(S['angle'])<.1:
        lap+= 1
    prev_distance_from_start= S['distFromStart']
    if not lap: 
        T.laplength= max(S['distFromStart'],T.laplength)
    elif lap == 1 and not T.usable_model: 
        learn_track(R['steer'],S['angle'],S['track'],S['distFromStart'])
    elif c.stage == 3:
        pass 
    else: 
        if not learn_final: 
            learn_track_final(T.laplength)
            T.post_process_track()
            learn_final= True
        if T.laplength:
            properlap= S['distRaced']/T.laplength
        else:
            properlap= 0
        if c.stage == 0 and lap < 4: 
            T.record_badness(badness,S['distFromStart'])
    S['targetSpeed']= target_speed 
    target_speed= 70 
    badness= S['damage']
    return
def initialize_car(c):
    R= c.R.d
    R['gear']= 1 
    R['steer']= 0 
    R['brake']= 1 
    R['clutch']= 1 
    R['accel']= .22 
    R['focus']= 0 
    c.respond_to_server() 
if __name__ == "__main__":
    T= Track()
    C= snakeoil.Client()
    if C.stage == 1 or C.stage == 2:
        try:
            T.load_track(C.trackname)
        except:
            print "Could not load the track: %s" % C.trackname
            sys.exit()
        print "Track loaded!"
    initialize_car(C)
    C.S.d['stucktimer']= 0
    C.S.d['targetSpeed']= 0
    for step in xrange(C.maxSteps,0,-1):
 
        a=C.get_servers_input()
        drive(C,step)
        b=C.respond_to_server()
        if b!=None:
            print b
        '''
        if (a and b)!=None:
            with open("X.csv", "ab") as fp:
                wr = csv.writer(fp)
                wr.writerow(a)
            with open("Y.csv", "ab") as fp:
                wr = csv.writer(fp)
                wr.writerow(b)
                '''
    if not C.stage:  
        T.write_track(C.trackname) 
    C.R.d['meta']= 1
    C.respond_to_server()
    C.shutdown()
