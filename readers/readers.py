import importlib
from abc import abstractmethod, ABCMeta


try:
    import pyproj  # Import pyproj
except:
    try: 
        # ...alternatively use version included with Basemap
        from mpl_toolkits.basemap import pyproj
    except:
        raise ImportError('pyproj needed for coordinate transformations,'\
                          ' please install from ' \
                          'https://code.google.com/p/pyproj/')


class Readers(object):
    '''Single entry point towards driver data from several models'''

    def __init__(self):
        self.readers = []

    def add_reader(self, reader, arguments=None, variables=None, name=None):
        
        if isinstance(variables, str):
            variables = [variables]
        if isinstance(reader, str):
            # Import requested reader
            try:
                readerModule = importlib.import_module(
                                    'readers.reader_' + reader)
                reader = readerModule.Reader()
            except ImportError:
                raise ImportError('Reader ' + reader + ' (reader_' + 
                                  reader + '.py)' + ' not available')

        # Check if input class is of correct type
        if not isinstance(reader, Reader):
            raise TypeError('Please provide Reader object')
            
        # Check that reader class contains the requested variables
        if variables is not None:
            missingVariables = set(variables) - set(reader.variables)
            if missingVariables:
                raise ValueError('Missing variable: ' +
                                 str(list(missingVariables)))
        
        if name is not None:
            reader.name = name
        # Finally add new reader to list
        self.readers.append(reader)

    def list_environment_variables(self):
        variables = []
        for reader in self.readers:
            variables.extend(reader.variables)
        return variables
        
    def get_environment(self, variables, proj4, x, y, depth, time):
        if isinstance(variables, str):
            variables = [variables]

        missingVariables = set(variables) - set(
                                self.list_environment_variables())
        if missingVariables:
            raise ValueError('Missing variables: ' +
                             str(list(missingVariables)))



class Reader(object):
    __metaclass__ = ABCMeta
    '''Parent Reader class'''

    def __init__(self):
        # Common constructor for all readers

        # Set projection for coordinate transformations
        self.proj = pyproj.Proj(self.proj4)

    @abstractmethod
    def get_variables(self, requestedVariables, time=None,
                x=None, y=None, depth=None):
        pass

    def xy2lonlat(self, x, y):
       return self.proj(x, y, inverse=True)

    def lonlat2xy(self, lon, lat):
       return self.proj(lon, lat, inverse=False)

    def check_arguments(self, variables, time, x, y, depth):
        # Check that required position and time are within
        # coverage of this reader, and that it can provide
        # the requested variable(s)
        for variable in variables:
            if variable not in self.variables:
                raise ValueError('Variable not available: ' + variable)
        if self.startTime is not None and time < self.startTime:
            raise ValueError('Outside time domain')
        if self.endTime is not None and time > self.endTime:
            raise ValueError('Outside time domain')
        if x.min() < self.xmin or x.max() > self.xmax:
            raise ValueError('x outside available domain')
        if y.min() < self.ymin or y.max() > self.ymax:
            raise ValueError('y outside available domain')

    def index_of_closest_time(self, requestedTime):
        # Temporarily assuming time steps are constant 
        indx = float((requestedTime - self.startTime).total_seconds()) / \
                float(self.timeStep.total_seconds())
        indx = int(round(indx))
        nearestTime = self.times[indx]
        return indx, nearestTime
        
    def __repr__(self):
        outStr = '===========================\n'
        outStr += 'Reader: ' + self.name + '\n'
        outStr += 'Projection: \n  ' + self.proj4 + '\n'
        outStr += '  xmin: %f   xmax: %f   step: %f\n' % (self.xmin, self.xmax, self.delta_x or 0)
        outStr += '  ymin: %f   ymax: %f   step: %f\n' % (self.ymin, self.ymax, self.delta_y or 0)
        corners = self.xy2lonlat([self.xmin, self.xmin, self.xmax, self.xmax],
                                 [self.ymax, self.ymin, self.ymax, self.ymin])
        outStr += '  Corners (lon, lat):\n'
        outStr += '    (%6.2f, %6.2f)  (%6.2f, %6.2f)\n' % (corners[0][0],
                                                           corners[1][0],
                                                           corners[0][2],
                                                           corners[1][2])
        outStr += '    (%6.2f, %6.2f)  (%6.2f, %6.2f)\n' % (corners[0][1],
                                                           corners[1][1],
                                                           corners[0][3],
                                                           corners[1][3]) 
        outStr += 'Available time range:\n'
        outStr += '  start: ' + str(self.startTime) + \
                  '   end: ' + str(self.endTime) + \
                  '   step: ' + str(self.timeStep) + '\n'
        outStr += 'Variables:\n'
        for variable in self.variables:
            outStr += '  ' + variable + '\n'
        outStr += '===========================\n'
        return outStr

        print self.variables
        print self.proj4