import numpy as np
from smith import smith_normal_form
from fractions import Fraction
from sys import maxint

def nontrivial(mat):
    return np.matrix.copy(mat[mat!=1])

class NDQF(object):
    '''Represents a negative definite quadratic form.'''
    
    @classmethod
    def rational_inverse(cls, diag, left, right):
        '''
        Returns inverse of a rational matrix m with Smith normal form decomp
        diag, (left, right). i.e. left * diag * right = m.
        Then m^(-1) = right^(-1)diag^(-1)left^(-1).
        '''
        def flip(n):
            if n == 0:
                return 0
            else:
                return Fraction(1, n)
        new_left = np.rint(right.I).astype(int) # inverse of right
        new_right = np.rint(left.I).astype(int) # inverse of left
        # right, left unimodular => inverse is also an integer matrix
        return new_left * np.vectorize(flip)(diag) * new_right 
        
    def __init__(self, mat):
        '''Creates a quadratic form from an appropriate
        array-like value.'''
        try:
            m = np.matrix(mat)
        except Exception as e:
            raise ValueError("Must be convertible to a numpy matrix.")
            #raise e
        '''if not square(m):
            raise ValueError("Must be a square array to create a quad form.")
        if not negative_definite(m):
            raise ValueError("Must be a negative definite matrix.")
        if not symmetric(m):
            raise ValueError("Must be a symmetric array.")'''
        self.mat = m
        d, (u, v) = smith_normal_form(m)
        self.decomp = (d, (u, v))
        self.mat_inverse = NDQF.rational_inverse(d, u, v)
        self.compute_affine_space()
        self.compute_homology()
         
    def eval(self, u, v, inverse=False):
        '''Evaluates the quadratic form on the vectors u and v. They should
        have appropriate lengths, but otherwise are autoconverted to the
        appropriate dimensions for Q(u, v) to be a scalar.'''
        u = np.matrix(u)
        v = np.matrix(v)
        if u.size == v.size == self.mat.shape[0]:
            u = u.reshape(1, u.size)
            v = v.reshape(v.size, 1)
            if inverse:
                return u * self.mat_inverse * v
            else:
                return u * self.mat * v
        else:
            raise ValueError("Inappropriately sized vectors for eval.")

    def compute_homology(self):
        # The ith row of V corresponds to ZZ/D[i, i] in the module
        # ZZ^d / mat ZZ^d
        D, (U, V) = self.decomp
        self.group = Hom_Group(D, V)
       
    def compute_affine_space(self):
        '''Finds the basepoint of the affine space associated to the 
        quadratic form. The rest can be found by the action of the group.'''
        self.basepoint = np.diagonal(self.mat) % 2

    def find_abs(self, alpha):
        '''Find the absolute value |alpha|^2 for the matrix, that is
        max_v (alpha(v))^2 / Q(v, v)'''
        return self.eval(alpha, alpha, inverse=True)[0,0] # get rid of matrix

    def find_rep(self, coef_list):
        '''Finds a representative of the class for the coeficient list.
        Returns the vector 'basepoint + c0 * gen[0] + c1 * gen[1]+ ...'''
        unsummed = [c * g for (c, g) in zip(coef_list, self.group.gen)]
        return self.basepoint + sum(unsummed)

    def correction_terms(self):
        '''Finds the correction terms assoctiated to the quadratic form,
        for each of the equivalance classes it finds the maximum by 
        iterating through the relation vectors of the group.'''
        coef_lists = lrange(self.group.structure)
        representatives = map(lambda l: self.find_rep(l), coef_lists) # elements of C_1(V)
        listofmaxes = []
        for rep in representatives: # for each equivalence class in C_1(V)
            maxval = -maxint-1 # smallest int            
            betagen = self.get_beta(rep)
            # find max in equivalence class (add 2q(V), use |a_i|<=-Q(e_i,e_i))
            # q(e_i)(v) = [ith row of Q]*v
            for beta in betagen:
                #alpha = rep + betagen(rep).next()
                alpha = rep + beta
                alphaval = self.find_abs(alpha)
                if alphaval > maxval:
                    maxval = alphaval
            listofmaxes.append(maxval)
        #disps = max_displacements(self.basepoint, self.group.rel)
        return listofmaxes
    
    def max_bounds(self, rep):
        '''
        Return list of all possible values in 2q(V) (note must be even) s.t. 
        alpha := rep + val satisfies |a_i| <= -Q(e_i, e_i)
        
        'max_list' - a list [lst_1, lst_2, ... lst_b] where lst_i is a list of 
                     possible values for a_i
        'max_list_sizes' - a list of the size of each list_i in 'max_list'
        '''
        diag_vals = [-self.mat[val, val] for val in range(self.mat.shape[0])]
        max_list = [[i for i in range(-ndiag-rep[index], ndiag+1-rep[index]) if i%2 == 0] for index, ndiag in enumerate(diag_vals)]
        max_list_sizes = [len(lst) for lst in max_list]
        return max_list, max_list_sizes
    
    def increment(self, counter, pos, diag):
        '''
        Increment list 'counter' in position 'pos' from the end.
        Modifies 'counter'. List 'diag' is the negative of the diagonal elements
        of Q; i.e. the 2nd output 'max_list_sizes' from max_bounds.
        
        Basically views counter as the coefficients in a weird base expansion.
        Also base expansion is 'read' left to right.
        When one digit reaches the max allowed value (base), it carries over
        to the digit to the right, and itself is set back to zero.
        '''
        if pos >= len(counter): # trying to increment when already at end
            raise ValueError('Cannot increment counter any further; at end')        
        if counter[pos] >= diag[pos]-1: # max allowed value at pos
            counter[pos] = 0 # reset to 0
            self.increment(counter, pos+1, diag)
        else: # not at max allowed value
            counter[pos] += 1
        return counter
    
    def get_beta(self, rep):
        '''
        Generates all possible values for beta, where beta is defined s.t.
        alpha := rep + beta satisfies |a_i|<=-Q(e_i,e_i)
        '''
        rep = np.array(rep)[0].tolist() # convert rep (numpy matrix) to list
        max_list, max_list_sizes = self.max_bounds(rep)
        max_list_sizes2 = [val-1 for val in max_list_sizes]
        length = self.mat.shape[0]        
        counter = [0 for i in range(length)] # which beta coords to pick        
        for i in range(reduce(lambda x, y: x*y, max_list_sizes)):
            beta = [max_list[i][counter[i]] for i in range(length)]
            yield beta
            # update counter
            if counter != max_list_sizes2:
                self.increment(counter, 0, max_list_sizes)
            else:
                return
    
    def get_equiv_class(self):
        '''
        Generates elements in equivalence class
        '''
        pass
    
    
class Hom_Group(object):
    '''A homology group.'''
    
    def __init__(self, diagonal, rows):
        '''Creates a new homology group using the list of invariant factors
        on the diagonal.'''
        invariant_factors = np.diagonal(diagonal)
        matters = nontrivial(invariant_factors)
        # structure = [n1, n2, .. nk] if H1(Y) ~ ZZ/n1 x ZZ/n2 x ... ZZ/nk
        self.structure = matters.tolist()
        group_rank = len(self.structure)
        vect_dim = diagonal.shape[0]
        # The bottom row vectors in rows are the ones that generate the 
        # quotient module, subject to the top rows congruent to zero.
        start = vect_dim - group_rank
        self.gen = [rows[i] for i in range(start, vect_dim)] # generating vectors
        self.rel = [rows[i] for i in range(0, start)] # relation vectors ( = 0 )
        return

    def __repr__(self):
        ''' Shows the structure of the group, as well as generators and
        relations.'''
        ret = []
        def rep(i):
            '''The string representation of Z/i'''
            i = i if i > 0 else -i
            if i == 0:
                return "Z"
            elif i == 1:
                return "1"
            else:
                return "Z/" + str(i) + "Z"
        reps = map(rep, self.structure)
        if reps:
            structure = reduce(lambda s, z: s + 'x' + z, reps)
        else:
            structure = "1"
        ret.append("Structure decomposition: H_1(Y) ~ " + structure + '.')
        ret.append("Generating vectors in order of invariant factor:")
        i = 0
        empty = True
        for row in self.gen:
            empty = False
            ret.append('    ' + str(row) + " has order " + 
                        str(self.structure[i]) + ".")
            i += 1
        if empty:
            ret.append("     (No generators, trivial)")
            empty = True
        ret.append("Relation vectors (congruent to 0):")
        for row in self.rel:
            empty = False
            ret.append('    ' + str(row))
        if empty:
            ret.append("     (No relations, free)")
        return '\n'.join(ret)

def lrange(index_list):
    '''Returns a generators that iterates over range(ind1) x range(ind2) ...'''
    if not index_list:
        yield []
    else:
        i = index_list[0]
        for i_sub in xrange(i):
            for l_sub in lrange(index_list[1:]):
                yield [i_sub] + l_sub

def nlrange(index_list):
    '''Returns a generator that is essentially range(-ind1+1, ind1) x ... 
    to traverse over a lattice.'''
    if not index_list:
        yield []
    else:
        i = index_list[0]
        for i_sub in xrange(-i + 1, i):
            for l_sub in nlrange(index_list[1:]):
                yield [i_sub] + l_sub


class Spin_Structure(object):
    '''A what?'''
    pass


b=NDQF([[-2,  0,  0,  1,  1],
 [ 0,-2, -1, -1, -1],
 [ 0, -1, -2, -1, -1],
 [ 1, -1, -1, -3, -2],
 [ 1, -1, -1, -2, -3]])

a=NDQF([[-2, -1, -1],[-1, -2, -1],[-1, -1, -2]])