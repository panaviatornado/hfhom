# Caltech SURF 2013
# FILE: gui_output.py
# 08.19.13

from Tkinter import *
import tkFileDialog

class OutputWindow(object):
    '''Print output'''
    def __init__(self, master, corr_terms, quad, inputinfo, condense=False,
                 showquad=False, showgraph=False, regions=[], showseifert=False,
                 seifertdata=None):
        self.master = master
        self.top = Toplevel(master)
        self.top.title('Output')
        self.corr = corr_terms
        self.quad = quad
        self.seifert = seifertdata # seifert data; output of alter_data
                                   # tuple (listdata, True/false)
        self.inputinfo = inputinfo # string, eg. knotilus archive num
        self.showquad = showquad # boolean or 1,0 to print quadratic form also
        
        Button(self.top, text='Save', command=self.save).grid(row=0, column=0)
        Button(self.top, text='Copy', command=self.copy).grid(row=0, column=1)
        Button(self.top, text='Close', command=self.top.destroy).grid(row=0,\
                                                                      column=2)
        
        self.output = Text(self.top, width=62)        
        if condense: # single line output
            self.output.insert(INSERT, '%s %s' % (inputinfo, str(self.corr)))
        else:
            self.output.insert(INSERT, '%s\n\nCorrection terms:\n%s\n' \
                               % (inputinfo, str(self.corr)))
            if showquad:
                self.output.insert(INSERT, '\nQuadratic form:\n%s\n' %str(quad))
            if showgraph:
                # recomputes everything, but it's not a bottleneck so ok
                Nodes=[NodeClass(i) for i in range(len(regions))]
                t = edges_regions(Nodes,regions)
                m = maximal_subtree(t, Nodes)            
                self.output.insert(INSERT, '\nGraph Commands:\n%s\n%s\n' \
                                   % (graph_plot(t), graph_plot(m)))
            if showseifert:
                self.output.insert(INSERT, 
                    '\nAltered Seifert data:%s, reversed = %s\n' %seifertdata)
        #self.output.configure(state=DISABLED) # read only
        self.output.grid(row=1, column=0, columnspan=3)
        
        scrollbar = Scrollbar(self.top)
        scrollbar.grid(row=1, column=4, sticky='n'+'s')     
        self.output.config(yscrollcommand=scrollbar.set)        
        scrollbar.config(command=self.output.yview)
        
    def save(self):
        '''Save output to file.'''
        options = {}
        options['defaultextension'] = '.txt'
        options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
        options['initialfile'] = 'corr_' + self.inputinfo + '.txt'
        filename = tkFileDialog.asksaveasfilename(**options)
        
        if filename:
            corr_file = open(filename, 'w')
            corr_file.write(self.output.get(1.0, END))
            corr_file.close()
            print 'Saved to %s' % filename
    
    def copy(self):
        '''Copy correction terms to clipboard.'''
        r = Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(self.output.get(1.0, END))
        r.destroy()
        print 'Copied to clipboard'