def bricks_to_geodataframe(polygons, bricks_array, gmina_id, count, adr_colname):
    polygons['brick'] = -1
    i = 0
    for brick in bricks_array:
        polygons.at[brick, 'brick'] = i
        i+=1 
    #Dodanie informacji o ilości punktów adresowych (po czyszczeniach i łączeniach)
    #Ponieważ przy agregacji używam funkcji "sum", wstawiając w każdym wierszu 1 uzyskam liczność
    polygons[adr_colname] = 1

    polygons = polygons.dissolve(by='brick', aggfunc='sum')
    polygons = polygons.drop(columns=['index', 'dissolve_column'])

    brick_ids = [str(gmina_id) + "_" + str(count) + "_" + str(i) for i in range(len(bricks_array))]
    polygons['Brick_ID'] = brick_ids

    return polygons