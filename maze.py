from random import choice
from re import match
from array import array

arrayOf = lambda size, fill=0, /: array('H', [fill for i in range(size)])

allEdges = lambda width, height, /: (*range(1, width - 1), *range(height * width - width + 1, width * height - 1), *range(width + 1, width * height + 1, width), *range(2 * width, width * height, width))

def pointsAroundPoint (point, width, height, /):
    points = []
    edges = (*allEdges(width, height), 0, width - 1, width * height - width + 1, width * height - 1)
    if ((point + 1) // width) * width + ((point + 1) % width) == point + 1 and point + 1 not in edges:
        points.append(point + 1)
    if ((point - 1) // width) * width + ((point - 1) % width) == point - 1 and point - 1 not in edges:
        points.append(point - 1)
    if point + width <= width * height - width and point + width not in edges:
        points.append(point + width)
    if point - width >= width and point - width not in edges:
        points.append(point - width)
    return points

def generateMaze(width, height):
    maze = arrayOf(width * height, 1)
    start = choice(tuple(allEdges(width, height)))
    while (end := choice(tuple(allEdges(width, height)))) == start or abs(start - end) in (1, width):
        continue
    print(start, end)
    maze[start] = maze[end] = maze[pointsAroundPoint(start, width, height)[0]] = maze[pointsAroundPoint(end, width, height)[0]] = 0
    return maze, width, height

def printMaze(maze, width, /):
    for i in range(len(maze) // width):
        print(' '.join([' #+'[n] for n in maze[width * i : width * (i + 1)]]))

def wellFormedInput(prompt, check, /):
    while  isinstance(msg := check(text := input(prompt)), str):
        print(msg or 'Invalid value')
    return text

def tryPlace(maze, t, place, end, /):
	if place not in t and maze[place] == 0:
		if place == end:
			return [*t, place], True
		else:
			return [*t, place], False
	return None, False

def pathFindMaze(maze, width, height, start, end, /):
   tried = [[start]]
   c = 1
   answer = None
   while True:
   	if len(tried) == 0:
   		print("No solutions found :(")
   		return
   	for t in tried:
   		last = t[-1]
   		if ((last + 1) // width) * width + ((last + 1) % width) == last + 1:
   			newT, finished = tryPlace(maze, t, last + 1, end)
   			if newT:
   				tried.append(newT)
   				if finished:
   					answer = tried[-1]
   					break
   		if ((last - 1) // width) * width + ((last - 1) % width) == last - 1:
   			newT, finished = tryPlace(maze, t, last - 1, end)
   			if newT:
   				tried.append(newT)
   				if finished:
   					answer = tried[-1]
   					break
   		if last + width < len(maze):
   			newT, finished = tryPlace(maze, t, last + width, end)
   			if newT:
   				tried.append(newT)
   				if finished:
   					answer = tried[-1]
   					break
   		if last - width > 0:
   			newT, finished = tryPlace(maze, t, last - width, end)
   			if newT:
   				tried.append(newT)
   				if finished:
   					answer = tried[-1]
   					break
   	else: # this runs if break is NOT called i.e. a solution has not been found
   		c += 1
   		tried = [e for e in tried if len(e) == c]
   		continue
   	break # only if solution IS found
   print("solution found:")
   for i in answer:
   	maze[i] = 2
   printMaze(maze, width)

def run():
    width = int(wellFormedInput('Enter the width of the maze: ', lambda w: match(r'^\s*0*([3-9]|[1-9]\d+)\s*$', w) or 'Invalid value. Value must be an integer larger than 3.'))
    height = int(wellFormedInput('Enter the height of the maze: ', lambda h: match(r'^\s*0*([3-9]|[1-9]\d+)\s*$', h) or 'Invalid value. Value must be an integer larger than 3.'))
    autoGenerate = wellFormedInput('Would you like to automatically generate the maze (yes/no)? ', lambda a: match(r'\s*(y(es?)?)|(no?)\s*', a) or 'Invalid response.' if a not in 'yes' else 'This isn\'t implemented yet. Please say no.').strip() in 'yes'
    start = -1
    end = -1
    if not autoGenerate:
        maze = arrayOf(0)
        i = 0
        while i < height:
            row = wellFormedInput(f'Enter row {i + 1} of the maze, using # for walls and spaces for things that aren\'t walls. Only two edge pieces can be blank overall.\n', \
                                  lambda r: (len(r) == width and r[0] == r[-1] == "#" and \
                                             (r.count(" ") <= 2 and "  " not in r) if i in (0, height - 1) else True)\
                                  or 'Invalid row.')
            if i in (0, height - 1):
                for s in (x for x, c in enumerate(row) if c == " "):
                    if start == -1:
                        start = i * width + s
                    elif end == -1:
                        end = i * width + s
                    else:
                        print('Invalid row - too many entrances/exits')
                        continue
            else:
                if ' ' == row[0]:
                    if start == -1:
                        start = i * width
                    elif end == -1:
                        end = i * width
                    else:
                        print('Invalid row - too many entrances/exits')
                        continue
                if ' ' == row[-1]:
                    if start == -1:
                        start = i * width + width - 1
                    elif end == -1:
                        end = i * width + width - 1
                    else:
                        print('Invalid row - too many entrances/exits')
                        continue
            maze.fromlist([' #'.index(c) for c in row])
            i += 1
               
        print('\nYour maze:\n')
        printMaze(maze, width)
           
    else:
        maze, start, end = generateMaze(width, height)
        printMaze(maze, width)
    print(start, end)
    print('\nSolution to maze:\n')
    pathFindMaze(maze, width, height, start, end)
   
while True:
    run()