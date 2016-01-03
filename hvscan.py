#!/usr/bin/env python
'''
process HV scan data for signal PMTs
book#3 p.68-75
20151230
'''

import csv
import graphUtils
from ROOT import TFile
import math
import numpy

class hvscan():
    def __init__(self):
        self.fn = '/Users/djaffe/Documents/Neutrinos/LDRD2010/OneTonPrototypeIn2-224/Installation/HVscan_20151230.csv'
        self.figdir = 'Figures/HVscan/'
        self.columns = {}
        self.colhdrs = []
        self.sgnlhdrs= []
        self.gU = graphUtils.graphUtils()
        return
    def process(self):
        '''
        read in the data
        empty column entries are assigned a value of -1
        '''
        columns = {}
        colhdrs = []
        sgnlhdrs= []
        with open(self.fn,'rU') as csvfile:
            rdr = csv.reader(csvfile,delimiter=',')
            first = True
            for l in rdr:
                if first:
                    first = False
                    for x in l:
                        if x!='':
                            colhdrs.append(x)
                            if x[0]=='s': sgnlhdrs.append(x)
                            columns[x] = []
                else:
                    for i,x in enumerate(l):
                        if i<len(colhdrs):
                            if x=='':
                                fx = -1.
                            elif int(x)==-1:
                                fx = -1.
                            else:
                                fx = float(x)
                            columns[colhdrs[i]].append(fx)
        print 'hvscan.process:',len(colhdrs),'column headers:',[x for x in colhdrs]
        self.columns = columns
        self.colhdrs = colhdrs
        self.sgnlhdrs= sgnlhdrs
        self.Graphs = {}
        return
    def winnow(self,Xin,Yin):
        '''
        return X,Y excluding negative values in input Yin
        '''
        X,Y = [],[]
        for x,y in zip(Xin,Yin):
            if y>=0.:
                X.append(x)
                Y.append(y)
        return X,Y
    def plotRaw(self):
        '''
        plot counts/10 sec for each HV value.
        exclude negative values
        '''
        colhdrs,columns = self.colhdrs,self.columns
        for icol,hdr in enumerate(colhdrs):
            Xin = [abs(x) for x in columns['HV']]
            if hdr!='HV':
                Yin = columns[hdr]
                X,Y = self.winnow(Xin,Yin)
                title = hdr + ' raw data'
                name = title.replace(' ','_')
                g = self.Graphs[name] = self.gU.makeTGraph(X,Y,title,name)
                self.gU.color(g,icol,icol,setMarkerColor=True)
                self.gU.drawGraph(g,figDir=self.figdir,option='AP')
        return
    def calcRate(self,Xin,Yin,LEDin):
        Rate,dRate = {},{}
        X = []
        for x in Xin:
            if x not in X: X.append(x)
        X.sort()
        for hv in X:
            cts = []
            bkg = []
            led = []
            for i,x in enumerate(Xin):
                if hv==x:
                    if Yin[i]>=0.:
                        if LEDin[i]==0:
                            bkg.append(Yin[i])
                        else:
                            cts.append(Yin[i])
                            led.append(LEDin[i])
            if len(cts)>0:
                abkg,vbkg = self.meanAndVar(bkg)
                acts,vcts = self.meanAndVar(cts)
                aled,vled = self.meanAndVar(led)
                r = (acts - abkg)/aled
                vr = vcts/aled/aled + vbkg/aled/aled + vled/aled/aled*r*r
                if math.isnan(r):
                    print 'nan?','hv',hv,'bkg',bkg,'cts',cts,'led',led
                Rate[hv] = r
                dRate[hv] = math.sqrt(vr)
                #print 'hv',hv,'averages bkg,cts,led',abkg,acts,aled,'r+-dr',r,math.sqrt(vr)

        X,Y,eX,eY = [],[],[],[]
        for hv in sorted(Rate):
            X.append(hv)
            eX.append(0.)
            Y.append(Rate[hv])
            eY.append(dRate[hv])
        return X,Y,eX,eY
    def meanAndVar(self,y):
        '''
        return mean and variance of input list
        '''
        a = numpy.ma.mean(y)
        v = numpy.ma.var(y)
        return a,v        
    def plotRate(self):
        '''
        plot mean and RMS signal PMT rates after background subtraction
        and normalized by the number of LED triggers
        '''
        tmg = self.gU.makeTMultiGraph('bkgd_sub_rates')
        nmg = self.gU.makeTMultiGraph('normed_bkgd_sub_rates')
        colhdrs,sgnlhdrs,columns = self.colhdrs,self.sgnlhdrs,self.columns
        for icol,hdr in enumerate(colhdrs):
            #print hdr
            if hdr in sgnlhdrs:
                Xin = [abs(x) for x in columns['HV']]
                LEDcts = columns['led']
                Yin = columns[hdr]
                X,Y,eX,eY = self.calcRate(Xin,Yin,LEDcts)
                #print X,Y,eX,eY
                title = hdr + ' rate per LED trigger'
                name = title.replace(' ','_')
                g = self.Graphs[name] = self.gU.makeTGraph(X,Y,title,name,ex=eX,ey=eY)
                self.gU.color(g,icol,icol,setMarkerColor=True)
                self.gU.drawGraph(g,figDir=self.figdir,option='AP')
                tmg.Add(g)
                
                maxY = max(Y)
                eY = [x/maxY for x in eY]
                Y  = [y/maxY for y in Y]
                title = hdr + ' normed rate per LED trigger'
                name = title.replace(' ','_')
                g = self.Graphs[name] = self.gU.makeTGraph(X,Y,title,name,ex=eX,ey=eY)
                self.gU.color(g,icol,icol,setMarkerColor=True)
                self.gU.drawGraph(g,figDir=self.figdir,option='AP')
                nmg.Add(g)
                
        self.gU.drawMultiGraph(tmg,figdir=self.figdir,abscissaIsTime=False,xAxisLabel='HV(volts)',yAxisLabel='rate per LED trigger')
        self.gU.drawMultiGraph(nmg,figdir=self.figdir,abscissaIsTime=False,xAxisLabel='HV(volts)',yAxisLabel='normed rate per LED trigger')
        return
    def plotInfo(self):
        '''
        plot useful info
        '''
        colhdrs,sgnlhdrs,columns = self.colhdrs,self.sgnlhdrs,self.columns
        hlist = []
        for hdr in ['cosmic','led']:
            X = []
            for x in columns[hdr]:
                if x>=0.: X.append(x/10.)
            title = hdr +' rate per sec'
            name = title.replace(' ','_')
            nx,xmi,xma = 15,-0.05,1.45
            if hdr=='led': nx,xmi,xma = 40,995.,1005.
            h = self.gU.makeTH1D(X,title,name,nx=nx,xmi=xmi,xma=xma)
            hlist.append(h)
        self.gU.drawMultiHists(hlist,figdir=self.figdir)
        return
if __name__ == '__main__' :
    r = hvscan()
    r.process()
    r.plotInfo()
    r.plotRaw()
    r.plotRate()
    
