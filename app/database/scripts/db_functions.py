#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import yaml, os, psycopg2, glob


def bulk_compute_profile(db_name, user, port, host, password, size):
    import psycopg2

    con = psycopg2.connect("dbname='%s' user='%s' port = '%s' host='%s' password='%s'" % (db_name,user,str(port),host,password))
    cursor = con.cursor()

    cursor.execute('SELECT count(*) FROM ways;')
    cnt_ways = cursor.fetchall()[0][0]

    cursor.execute("""
        DROP TABLE IF EXISTS ways_profile;
        
        CREATE TABLE ways_profile (
        way_id bigint NOT NULL,
        elevation decimal NOT NULL,
        geom geometry NOT NULL
        );
        
        CREATE INDEX way_id_idx ON ways_profile USING btree(way_id);
        CREATE INDEX geom_idx ON ways_profile USING gist(geom);
    """)

    con.commit()

    batches = range(int(cnt_ways / size)+1)

    # TODO: Enable threading/parallelism
    for b in batches:
        sql = """
            WITH segments AS (
                SELECT id FROM ways LIMIT {0} OFFSET {1}
            )
            
            
            INSERT INTO ways_profile
            SELECT seg.return_id as way_id, seg.elevs as elevation, seg.return_geom as geom                         
            FROM segments s,
            LATERAL get_slope_profile_precompute(s.id) seg;        
        """.format(size, b*size)

        cursor.execute(sql)
        con.commit()

# bulk_compute_profile('goat','goat','65432','localhost','earlmanigault', 1000)

def bulk_compute_slope(db_name,user,port,host,password):
    import psycopg2

    con = psycopg2.connect("dbname='%s' user='%s' port = '%s' host='%s' password='%s'" % (db_name,user,str(port),host,password))
    cursor = con.cursor()

    cursor.execute('SELECT count(*) FROM ways;')
    cnt_ways = cursor.fetchall()[0][0]

    sql_way_ids = '''SELECT id
    FROM ways 
    WHERE class_id::text NOT IN(SELECT UNNEST(select_from_variable_container('excluded_class_id_cycling')));'''
    cursor.execute(sql_way_ids)
    way_ids = cursor.fetchall()

    cnt = 0
    for i in way_ids:
    
        cnt = cnt + 1 
        if (cnt/1000).is_integer():
            print('Impedance for %s out of %s ways' % (cnt,cnt_ways)) 
            con.commit()

        sql_compute_slope = 'SELECT update_impedance(%s::integer)' % (i[0])
        cursor.execute(sql_compute_slope)
#bulk_compute_slope('goat','goat','5432','localhost','earlmanigault')


def find_newest_dump(namespace):
    import os
    fnames = []
    for file in os.listdir("/opt/backups"):
        if file.endswith(".sql") and namespace == file.split('_')[0]:
            fnames.append(file)
    newest_file = sorted(fnames)[-1]

    return newest_file


