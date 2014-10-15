'''
TriSurfaceVector.py


!!! Still in alpha version !!!
'''

import re

import numpy as np
import matplotlib.tri as tri

import CoordinateTransformation as coorTrans


class TriSurfaceVector(object):
    '''
    class TriSurfaceVector
    '''
    
    # constructors #
    #--------------#
    
    def __init__(self, x, y, vx, vy, vz, triangles=None, mask=None, interpolation='cubic',kind='geom'):
        '''
        base constructor from a list of x, y and z. list of triangles and mask 
        optional.
        
        Arguments:
            *x*: numpy array of shape (npoints).
             x-coordinates of grid points.
    
            *y*: numpy array of shape (npoints).
             y-coordinates of grid points.
             
            *vx*: numpy array of shape (npoints).
             Vector componant in z direction
             
            *vy*: numpy array of shape (npoints).
             Vector componant in y direction
             
             *vz*: numpy array of shape (npoints).
             Vector componant in z direction

            *triangles*: integer array of shape (ntri,3).
             For each triangle, the indices of the three points that make
             up the triangle, ordered in an anticlockwise manner. If no
             triangles is passed, a Delauney triangulation is computed. 
             Default=None.
             
            *mask*: optional boolean array of shape (ntri).
             Which triangles are masked out.
             
            *interpoation*: python string.
             type of interpolation used if needed. "cubic" or "linear"
             
            
            *kind*
        '''

        self.triangulation = tri.Triangulation(x, y, triangles=triangles, mask=None)

        self.vx=np.asarray(vx)
        self.vy=np.asarray(vy)
        self.vz=np.asarray(vz)
        
    
        self.__interType = interpolation
        self.__interKind  = kind

        
        
        if self.__interType=='cubic':
            self.vxinter = tri.CubicTriInterpolator(self.triangulation, self.vx, kind=self.__interKind)
            self.vyinter = tri.CubicTriInterpolator(self.triangulation, self.vy, kind=self.__interKind)
            self.vzinter = tri.CubicTriInterpolator(self.triangulation, self.vz, kind=self.__interKind)
        elif self.__interType=='linear':
            self.vxinter = tri.LinearTriInterpolator(self.triangulation, self.vx)
            self.vyinter = tri.LinearTriInterpolator(self.triangulation, self.vy)
            self.vzinter = tri.LinearTriInterpolator(self.triangulation, self.vz)
        else:
            raise ValueError('Interpolation must be "cubic" or "linear".')
            
            
        
        self.data = dict()
        self.datainter = dict()
        
 
        
    @classmethod
    def readFromFoamFile(cls,
                         varsFile,
                         pointsFile,
                         facesFile,
                         viewAnchor,
                         xViewBasis,
                         yViewBasis,
                         srcBasisSrc=[[1,0,0],[0,1,0],[0,0,1]],
                         mask=None,
                         interpolation='cubic',
                         kind='geom'):
        '''
        Construct from a surface saved  by OpenFOAM in foamFile format.
        '''
        # check and convert arguments
        srcBasisSrc = np.array(srcBasisSrc,dtype=float)
        if srcBasisSrc.shape!=(3,3):
            raise ValueError('srcBasis must be a 3x3 matrix')
            
        xViewBasis = np.array(xViewBasis,dtype=float)
        yViewBasis = np.array(yViewBasis,dtype=float)
        if xViewBasis.shape!=(3,) or yViewBasis.shape!=(3,):
            raise ValueError('xViewBasis.shape and yViewBasis. ',
                             'shape must be equal to (3,)')
            
        # get the basis and the transformation object
        tgtBasisSrc = np.zeros((3,3))
        tgtBasisSrc[:,0] = xViewBasis        
        tgtBasisSrc[:,1] = yViewBasis
        tgtBasisSrc[:,2] = np.cross(xViewBasis,yViewBasis)
        afftrans = coorTrans.AffineTransfomation(srcBasisSrc,tgtBasisSrc,viewAnchor)

        # get x and y vector (in ptTrt)
        ptsSrc = parseFoamFile(pointsFile)
        ptsTgt = np.zeros((ptsSrc.shape[0],ptsSrc.shape[1]))
        for i in range(ptsSrc.shape[0]):
            ptsTgt[i,:] = afftrans.srcToTgt(ptsSrc[i,:])
            
        #get triangles
        triangles = parseFoamFile(facesFile)[:,1:4]
        
        #get vectors
        vectors = parseFoamFile(varsFile)
        

        # feed x, y and triangles to the base constructor
        #(self, x, y, vx, vy, vz, triangles=None, mask=None, interpolation='cubic',kind='geom')
        return cls(x=ptsTgt[:,0],
                   y=ptsTgt[:,1],
                   vx=vectors[:,0],
                   vy=vectors[:,0],
                   vz=vectors[:,0],
                   triangles=triangles,
                   mask=mask,
                   interpolation=interpolation,
                   kind=kind)
 
       
    @classmethod
    def readFromVTK(cls):
        '''
        Construct from a surface saved by OpenFOAM in VTK format.
        '''
        raise NotImplementedError('The method is not implemented')
  
    # getter and setter #
    #-------------------#

    def x(self):
        '''
        Get x coordinate of the grid points.
        '''
        return self.triangulation.x
        
        
    def y(self):
        '''
        Get y coordinate of the grid points.
        '''
        return self.triangulation.y
        
        
    def triangles(self):
        '''
        Get trangles from the grid.
        '''
        return self.triangulation.triangles
        
    
    # class methods #
    #---------------#
#    def rawGrad(self):
#        '''
#        Calculate and save the gradient at all (self.x,self.y) locations.
#        If x and y have a shape of (npts), z a shape of (npts,dim), than
#        the gradient has a shape of (npts,2,dim).
#        Example for a scalar field s:
#            * dsdx = self['grad'][:,0,0] or   self['grad'][:,0]
#            * dsdy = self['grad'][:,1,0] or   self['grad'][:,1]
#        Example for a vector field (u,v,w):
#            dudx = self['grad'][:,0,0]
#            dudy = self['grad'][:,1,0]
#            dvdx = self['grad'][:,0,1]
#            dvdy = self['grad'][:,1,1]
#            dwdx = self['grad'][:,0,2]
#            dwdy = self['grad'][:,1,2]
#        '''
#        self.create_interpolator()
#        self.data['grad'] = np.array([self.interpolator[i].gradient(self.triangulation.x,self.triangulation.y) for i in range(self.zsize())]).T

#    def gradient(self,x,y):
#        '''
#        Return gradient at location (x,y). x,y can be an array.
#        If x and y have a shape of (npts), z a shape of (npts,dim), than
#        the gradient has a shape of (npts,2,dim).
#        Example for a scalar field s:
#            * dsdx = self['grad'][:,0,0] or   self['grad'][:,0]
#            * dsdy = self['grad'][:,1,0] or   self['grad'][:,1]
#        Example for a vector field (u,v,w):
#            dudx = self['grad'][:,0,0]
#            dudy = self['grad'][:,1,0]
#            dvdx = self['grad'][:,0,1]
#            dvdy = self['grad'][:,1,1]
#            dwdx = self['grad'][:,0,2]
#            dwdy = self['grad'][:,1,2]
#        '''
#        # x and y must be numpy array
#        x = np.asarray(x, dtype=np.float)
#        y = np.asarray(y, dtype=np.float)
#        self.create_interpolator()
#        return np.array([self.interpolator[i].gradient(x,y) for i in range(self.zsize())]).T
                
        
        
#    def interpolate(self,x,y):
#        '''
#        Return interpolated value at location (x,y). x and y can be arrays. The
#        member variable interpolation can also be used directly.
#        '''
#        # no need to convert x and y in numpy array
#        self.create_interpolator()
#        return np.array([self.interpolator[i](x,y) for i in range(self.zsize())]).T

        

#    def create_velocityInterpolator(self):
#        '''
#        Create the list of interpolator object.
#        '''
#        pass
#            
#
#    def __iter__(self):
#        '''
#        Iterable on member "data".
#        '''
#        return self.data.itervalues()
#
#    def __getitem__(self, key):
#        '''
#        Getter for key "key" on member dictionnary "data"
#        '''
#        return self.data[key]
#
#    def __setitem__(self, key, item):
#        '''
#        Setter for key "key" on member dictionnary "data"
#        '''
#        self.data[key] = item

        
    

            


def parseFoamFile(foamFile):
    '''
    Parse a foamFile generated by the OpenFOAM sample tool or sampling library.
    
    Note:
        * It's a primitiv parse, do not add header in your foamFile!
        * Inline comment are allowed only from line start. c++ comment style.
        * It's REALLY a primitive parser!!!
        
    Arguments:
        * foamFile: [str()] Path of the foamFile

    Returns:
        * output: [numpy.array()] data store in foamFile
    '''
    output = []
    catchFirstNb = False
    istream = open(foamFile, 'r')
    for line in istream: 
        # This regex finds all numbers in a given string.
        # It can find floats and integers writen in normal mode (10000) or
        # with power of 10 (10e3).
        match = re.findall('[-+]?\d*\.?\d+e*[-+]?\d*', line)
        if (line.startswith('//')):
            pass
        if (catchFirstNb==False and len(match)==1):
            catchFirstNb = True
        elif (catchFirstNb==True and len(match)>0):
            matchfloat = list()
            for nb in match:                
                matchfloat.append(float(nb))
            output.append(matchfloat)
        else:
            pass
    istream.close()
    return np.array(output)  