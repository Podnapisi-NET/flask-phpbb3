INSERT INTO phpbb_topics(
            topic_id, forum_id, 
            topic_title, topic_time, topic_first_poster_name, topic_first_post_id, topic_type)
    VALUES (0,0,'naslov teme 0',10,'ime',1,3),
    (1,0,'naslov teme 1',13,'drugi poster',2,3),
    (2,0,'naslov teme 2',200,'post it',0,3),
    (3,0,'naslov teme 3',256,'posted it',3,3);



    INSERT INTO phpbb_posts(post_id,post_subject,post_text
    )
    VALUES
    (1,'prva tema', 'bla'),
    (2,'druga tema','blabla'),
    (0,'tretja tema','blablabla'),
    (3,'tretja tema','bla krat 4');
    
