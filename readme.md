# Steps

## Preps
1. Get the closest point on the line for the input points
2. Parametrize the polyline starting from left bottom most point and counter clockwise orientation
3. Get the parameter value of the points and save it in dxf file as bounds

## Operation
1. Move an object along a vector
2. Constraint check. if the new distance is within parameter or not
3. On and off layers in the dxf file
4. Save the current dxf as an image

## RASA
1. change position flow
    1. Object
    2. position
    3. if object is not door then give rejection message
2. List capabilities
    1. Change position
    2. Future things
    3. Display control


## RAG
1. Each layer name as an embedding
2. 
