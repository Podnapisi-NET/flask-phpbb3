-- A poor man's phpbb3 copy
create table phpbb_users (
    user_id integer primary key,
    user_type smallint not null default 0,
    group_id integer not null default 3,
    user_permissions text not null default '',
    user_perm_from integer not null default 0,
    user_ip character varying(40) not null default ''::character varying,
    user_regdate integer not null default 0,
    username varchar not null default ''::character varying,
    username_clean varchar not null default ''::character varying,
    user_password character varying(255) not null default ''::character varying,
    user_passchg integer not null default 0,
    user_email character varying(100) not null default ''::character varying,
    user_email_hash bigint not null default (0)::bigint,
    user_birthday character varying(10) not null default ''::character varying,
    user_lastvisit integer not null default 0,
    user_lastmark integer not null default 0,
    user_lastpost_time integer not null default 0,
    user_lastpage character varying(200) not null default ''::character varying,
    user_last_confirm_key character varying(10) not null default ''::character varying,
    user_last_search integer not null default 0,
    user_warnings smallint not null default (0)::smallint,
    user_last_warning integer not null default 0,
    user_login_attempts smallint not null default (0)::smallint,
    user_inactive_reason smallint not null default (0)::smallint,
    user_inactive_time integer not null default 0,
    user_posts integer not null default 0,
    user_lang character varying(30) not null default ''::character varying,
    user_timezone character varying(100) not null default ''::character varying,
    user_dateformat character varying(64) not null default 'd M Y H:i'::character varying,
    user_style integer not null default 0,
    user_rank integer not null default 0,
    user_colour character varying(6) not null default ''::character varying,
    user_new_privmsg integer not null default 0,
    user_unread_privmsg integer not null default 0,
    user_last_privmsg integer not null default 0,
    user_message_rules smallint not null default (0)::smallint,
    user_full_folder integer not null default (-3),
    user_emailtime integer not null default 0,
    user_topic_show_days smallint not null default (0)::smallint,
    user_topic_sortby_type character varying(1) not null default 't'::character varying,
    user_topic_sortby_dir character varying(1) not null default 'd'::character varying,
    user_post_show_days smallint not null default (0)::smallint,
    user_post_sortby_type character varying(1) not null default 't'::character varying,
    user_post_sortby_dir character varying(1) not null default 'a'::character varying,
    user_notify smallint not null default (0)::smallint,
    user_notify_pm smallint not null default (1)::smallint,
    user_notify_type smallint not null default (0)::smallint,
    user_allow_pm smallint not null default (1)::smallint,
    user_allow_viewonline smallint not null default (1)::smallint,
    user_allow_viewemail smallint not null default (1)::smallint,
    user_allow_massemail smallint not null default (1)::smallint,
    user_options integer not null default 230271,
    user_avatar character varying(255) not null default ''::character varying,
    user_avatar_type character varying(255) not null default ''::character varying,
    user_avatar_width smallint not null default (0)::smallint,
    user_avatar_height smallint not null default (0)::smallint,
    user_sig text not null default ''::text,
    user_sig_bbcode_uid character varying(8) not null default ''::character varying,
    user_sig_bbcode_bitfield character varying(255) not null default ''::character varying,
    user_jabber character varying(255) not null default ''::character varying,
    user_actkey character varying(32) not null default ''::character varying,
    user_newpasswd character varying(255) not null default ''::character varying,
    user_form_salt character varying(32) not null default ''::character varying,
    user_new smallint not null default (1)::smallint,
    user_reminded smallint not null default (0)::smallint,
    user_reminded_time integer not null default 0
);

insert into phpbb_users (
    user_id
    ,username
    , username_clean
) values (
    1
    ,'Anonymous'
    , 'anonymous'
);

create table phpbb_sessions_keys (
    key_id character(32) not null default ''::bpchar,
    user_id integer not null default 0,
    last_ip character varying(40) not null default ''::character varying,
    last_login integer not null default 0
);

create table phpbb_sessions (
    session_id  character(32)  not null default ''::bpchar,
    session_user_id  integer  not null default 0,
    session_forum_id  integer  not null default 0,
    session_last_visit  integer  not null default 0,
    session_start  integer  not null default 0,
    session_time  integer  not null default 0,
    session_ip  character varying(40)  not null default ''::character varying,
    session_browser  character varying(150)  not null default ''::character varying,
    session_forwarded_for  character varying(255)  not null default ''::character varying,
    session_page  character varying(255)  not null default ''::character varying,
    session_viewonline  smallint  not null default (1)::smallint,
    session_autologin  smallint  not null default (0)::smallint,
    session_admin  smallint  not null default (0)::smallint
);

create table phpbb_user_group (
    group_id  integer  not null default 0,
    user_id  integer  not null default 0,
    group_leader  smallint  not null default (0)::smallint,
    user_pending  smallint  not null default (1)::smallint
);

create table phpbb_groups (
    group_id  integer  primary key,
    group_type  smallint  not null default (1)::smallint,
    group_founder_manage  smallint  not null default (0)::smallint,
    group_skip_auth  smallint  not null default (0)::smallint,
    group_name  varchar  not null default ''::character varying,
    group_desc  character varying(4000)  not null default ''::character varying,
    group_desc_bitfield  character varying(255)  not null default ''::character varying,
    group_desc_options  integer  not null default 7,
    group_desc_uid  character varying(8)  not null default ''::character varying,
    group_display  smallint  not null default (0)::smallint,
    group_avatar  character varying(255)  not null default ''::character varying,
    group_avatar_type  character varying(255)  not null default ''::character varying,
    group_avatar_width  smallint  not null default (0)::smallint,
    group_avatar_height  smallint  not null default (0)::smallint,
    group_rank  integer  not null default 0,
    group_colour  character varying(6)  not null default ''::character varying,
    group_sig_chars  integer  not null default 0,
    group_receive_pm  smallint  not null default (0)::smallint,
    group_message_limit  integer  not null default 0,
    group_max_recipients  integer  not null default 0,
    group_legend  integer  not null default 0
);

create table phpbb_acl_options (
    auth_option_id  integer  primary key,
    auth_option  character varying(50)  not null default ''::character varying,
    is_global  smallint  not null default (0)::smallint,
    is_local  smallint  not null default (0)::smallint,
    founder_only  smallint  not null default (0)::smallint
);

create table phpbb_notifications (
    notification_id  integer  primary key,
    notification_type_id  smallint  not null default (0)::smallint,
    item_id  integer  not null default 0,
    item_parent_id  integer  not null default 0,
    user_id  integer  not null default 0,
    notification_read  smallint  not null default (0)::smallint,
    notification_time  integer  not null default 1,
    notification_data  character varying(4000)  not null default ''::character varying
);

create table phpbb_notification_types (
    notification_type_id  smallint  primary key,
    notification_type_name  character varying(255)  not null default ''::character varying,
    notification_type_enabled  smallint  not null default (1)::smallint
);


CREATE TABLE phpbb_topics (
    topic_id integer DEFAULT 0 NOT NULL,
    forum_id integer DEFAULT 0 NOT NULL,
    icon_id integer DEFAULT 0 NOT NULL,
    topic_attachment smallint DEFAULT (0)::smallint NOT NULL,
    topic_reported smallint DEFAULT (0)::smallint NOT NULL,
    topic_title character varying(255) DEFAULT ''::character varying NOT NULL,
    topic_poster integer DEFAULT 0 NOT NULL,
    topic_time integer DEFAULT 0 NOT NULL,
    topic_time_limit integer DEFAULT 0 NOT NULL,
    topic_views integer DEFAULT 0 NOT NULL,
    topic_status smallint DEFAULT (0)::smallint NOT NULL,
    topic_type smallint DEFAULT (0)::smallint NOT NULL,
    topic_first_post_id integer DEFAULT 0 NOT NULL,
    topic_first_poster_name character varying(255) DEFAULT ''::character varying NOT NULL,
    topic_first_poster_colour character varying(6) DEFAULT ''::character varying NOT NULL,
    topic_last_post_id integer DEFAULT 0 NOT NULL,
    topic_last_poster_id integer DEFAULT 0 NOT NULL,
    topic_last_poster_name character varying(255) DEFAULT ''::character varying NOT NULL,
    topic_last_poster_colour character varying(6) DEFAULT ''::character varying NOT NULL,
    topic_last_post_subject character varying(255) DEFAULT ''::character varying NOT NULL,
    topic_last_post_time integer DEFAULT 0 NOT NULL,
    topic_last_view_time integer DEFAULT 0 NOT NULL,
    topic_moved_id integer DEFAULT 0 NOT NULL,
    topic_bumped smallint DEFAULT (0)::smallint NOT NULL,
    topic_bumper integer DEFAULT 0 NOT NULL,
    poll_title character varying(255) DEFAULT ''::character varying NOT NULL,
    poll_start integer DEFAULT 0 NOT NULL,
    poll_length integer DEFAULT 0 NOT NULL,
    poll_max_options smallint DEFAULT (1)::smallint NOT NULL,
    poll_last_vote integer DEFAULT 0 NOT NULL,
    poll_vote_change smallint DEFAULT (0)::smallint NOT NULL,
    topic_visibility smallint DEFAULT (0)::smallint NOT NULL,
    topic_delete_time integer DEFAULT 0 NOT NULL,
    topic_delete_reason character varying(255) DEFAULT ''::character varying NOT NULL,
    topic_delete_user integer DEFAULT 0 NOT NULL,
    topic_posts_approved integer DEFAULT 0 NOT NULL,
    topic_posts_unapproved integer DEFAULT 0 NOT NULL,
    topic_posts_softdeleted integer DEFAULT 0 NOT NULL,
    CONSTRAINT phpbb_topics_forum_id_check CHECK ((forum_id >= 0)),
    CONSTRAINT phpbb_topics_icon_id_check CHECK ((icon_id >= 0)),
    CONSTRAINT phpbb_topics_poll_last_vote_check CHECK ((poll_last_vote >= 0)),
    CONSTRAINT phpbb_topics_poll_length_check CHECK ((poll_length >= 0)),
    CONSTRAINT phpbb_topics_poll_start_check CHECK ((poll_start >= 0)),
    CONSTRAINT phpbb_topics_poll_vote_change_check CHECK ((poll_vote_change >= 0)),
    CONSTRAINT phpbb_topics_topic_attachment_check CHECK ((topic_attachment >= 0)),
    CONSTRAINT phpbb_topics_topic_bumped_check CHECK ((topic_bumped >= 0)),
    CONSTRAINT phpbb_topics_topic_bumper_check CHECK ((topic_bumper >= 0)),
    CONSTRAINT phpbb_topics_topic_delete_time_check CHECK ((topic_delete_time >= 0)),
    CONSTRAINT phpbb_topics_topic_delete_user_check CHECK ((topic_delete_user >= 0)),
    CONSTRAINT phpbb_topics_topic_delete_user_check1 CHECK ((topic_delete_user >= 0)),
    CONSTRAINT phpbb_topics_topic_first_post_id_check CHECK ((topic_first_post_id >= 0)),
    CONSTRAINT phpbb_topics_topic_first_post_id_check1 CHECK ((topic_first_post_id >= 0)),
    CONSTRAINT phpbb_topics_topic_id_check CHECK ((topic_id >= 0)),
    CONSTRAINT phpbb_topics_topic_last_post_id_check CHECK ((topic_last_post_id >= 0)),
    CONSTRAINT phpbb_topics_topic_last_post_id_check1 CHECK ((topic_last_post_id >= 0)),
    CONSTRAINT phpbb_topics_topic_last_post_time_check CHECK ((topic_last_post_time >= 0)),
    CONSTRAINT phpbb_topics_topic_last_poster_id_check CHECK ((topic_last_poster_id >= 0)),
    CONSTRAINT phpbb_topics_topic_last_poster_id_check1 CHECK ((topic_last_poster_id >= 0)),
    CONSTRAINT phpbb_topics_topic_last_view_time_check CHECK ((topic_last_view_time >= 0)),
    CONSTRAINT phpbb_topics_topic_moved_id_check CHECK ((topic_moved_id >= 0)),
    CONSTRAINT phpbb_topics_topic_moved_id_check1 CHECK ((topic_moved_id >= 0)),
    CONSTRAINT phpbb_topics_topic_poster_check CHECK ((topic_poster >= 0)),
    CONSTRAINT phpbb_topics_topic_poster_check1 CHECK ((topic_poster >= 0)),
    CONSTRAINT phpbb_topics_topic_posts_approved_check CHECK ((topic_posts_approved >= 0)),
    CONSTRAINT phpbb_topics_topic_posts_softdeleted_check CHECK ((topic_posts_softdeleted >= 0)),
    CONSTRAINT phpbb_topics_topic_posts_unapproved_check CHECK ((topic_posts_unapproved >= 0)),
    CONSTRAINT phpbb_topics_topic_reported_check CHECK ((topic_reported >= 0)),
    CONSTRAINT phpbb_topics_topic_time_check CHECK ((topic_time >= 0)),
    CONSTRAINT phpbb_topics_topic_time_limit_check CHECK ((topic_time_limit >= 0)),
    CONSTRAINT phpbb_topics_topic_views_check CHECK ((topic_views >= 0))
);
ALTER TABLE ONLY phpbb_topics
    ADD CONSTRAINT phpbb_topics_pkey PRIMARY KEY (topic_id);
CREATE INDEX phpbb_topics_fid_time_moved ON phpbb_topics USING btree (forum_id, topic_last_post_time, topic_moved_id);
CREATE INDEX phpbb_topics_forum_id ON phpbb_topics USING btree (forum_id);
CREATE INDEX phpbb_topics_forum_id_type ON phpbb_topics USING btree (forum_id, topic_type);
CREATE INDEX phpbb_topics_forum_vis_last ON phpbb_topics USING btree (forum_id, topic_visibility, topic_last_post_id);
CREATE INDEX phpbb_topics_last_post_time ON phpbb_topics USING btree (topic_last_post_time);
CREATE INDEX phpbb_topics_latest_topics ON phpbb_topics USING btree (forum_id, topic_last_post_time, topic_last_post_id, topic_moved_id);
CREATE INDEX phpbb_topics_topic_visibility ON phpbb_topics USING btree (topic_visibility);


CREATE TABLE phpbb_posts (
    post_id integer DEFAULT 0 NOT NULL,
    topic_id integer DEFAULT 0 NOT NULL,
    forum_id integer DEFAULT 0 NOT NULL,
    poster_id integer DEFAULT 0 NOT NULL,
    icon_id integer DEFAULT 0 NOT NULL,
    poster_ip character varying(40) DEFAULT ''::character varying NOT NULL,
    post_time integer DEFAULT 0 NOT NULL,
    post_reported smallint DEFAULT (0)::smallint NOT NULL,
    enable_bbcode smallint DEFAULT (1)::smallint NOT NULL,
    enable_smilies smallint DEFAULT (1)::smallint NOT NULL,
    enable_magic_url smallint DEFAULT (1)::smallint NOT NULL,
    enable_sig smallint DEFAULT (1)::smallint NOT NULL,
    post_username character varying(255) DEFAULT ''::character varying NOT NULL,
    post_subject character varying(255) DEFAULT ''::character varying NOT NULL,
    post_text text DEFAULT ''::text NOT NULL,
    post_checksum character varying(32) DEFAULT ''::character varying NOT NULL,
    post_attachment smallint DEFAULT (0)::smallint NOT NULL,
    bbcode_bitfield character varying(255) DEFAULT ''::character varying NOT NULL,
    bbcode_uid character varying(8) DEFAULT ''::character varying NOT NULL,
    post_postcount smallint DEFAULT (1)::smallint NOT NULL,
    post_edit_time integer DEFAULT 0 NOT NULL,
    post_edit_reason character varying(255) DEFAULT ''::character varying NOT NULL,
    post_edit_user integer DEFAULT 0 NOT NULL,
    post_edit_count smallint DEFAULT (0)::smallint NOT NULL,
    post_edit_locked smallint DEFAULT (0)::smallint NOT NULL,
    post_visibility smallint DEFAULT (0)::smallint NOT NULL,
    post_delete_time integer DEFAULT 0 NOT NULL,
    post_delete_reason character varying(255) DEFAULT ''::character varying NOT NULL,
    post_delete_user integer DEFAULT 0 NOT NULL,
    CONSTRAINT phpbb_posts_enable_bbcode_check CHECK ((enable_bbcode >= 0)),
    CONSTRAINT phpbb_posts_enable_magic_url_check CHECK ((enable_magic_url >= 0)),
    CONSTRAINT phpbb_posts_enable_sig_check CHECK ((enable_sig >= 0)),
    CONSTRAINT phpbb_posts_enable_smilies_check CHECK ((enable_smilies >= 0)),
    CONSTRAINT phpbb_posts_forum_id_check CHECK ((forum_id >= 0)),
    CONSTRAINT phpbb_posts_icon_id_check CHECK ((icon_id >= 0)),
    CONSTRAINT phpbb_posts_post_attachment_check CHECK ((post_attachment >= 0)),
    CONSTRAINT phpbb_posts_post_delete_time_check CHECK ((post_delete_time >= 0)),
    CONSTRAINT phpbb_posts_post_delete_user_check CHECK ((post_delete_user >= 0)),
    CONSTRAINT phpbb_posts_post_delete_user_check1 CHECK ((post_delete_user >= 0)),
    CONSTRAINT phpbb_posts_post_edit_count_check CHECK ((post_edit_count >= 0)),
    CONSTRAINT phpbb_posts_post_edit_locked_check CHECK ((post_edit_locked >= 0)),
    CONSTRAINT phpbb_posts_post_edit_time_check CHECK ((post_edit_time >= 0)),
    CONSTRAINT phpbb_posts_post_edit_user_check CHECK ((post_edit_user >= 0)),
    CONSTRAINT phpbb_posts_post_edit_user_check1 CHECK ((post_edit_user >= 0)),
    CONSTRAINT phpbb_posts_post_id_check CHECK ((post_id >= 0)),
    CONSTRAINT phpbb_posts_post_postcount_check CHECK ((post_postcount >= 0)),
    CONSTRAINT phpbb_posts_post_reported_check CHECK ((post_reported >= 0)),
    CONSTRAINT phpbb_posts_post_time_check CHECK ((post_time >= 0)),
    CONSTRAINT phpbb_posts_poster_id_check CHECK ((poster_id >= 0)),
    CONSTRAINT phpbb_posts_poster_id_check1 CHECK ((poster_id >= 0)),
    CONSTRAINT phpbb_posts_topic_id_check CHECK ((topic_id >= 0)),
    CONSTRAINT phpbb_posts_topic_id_check1 CHECK ((topic_id >= 0))
);
ALTER TABLE ONLY phpbb_posts
    ADD CONSTRAINT phpbb_posts_pkey PRIMARY KEY (post_id);
CREATE INDEX phpbb_posts_forum_id ON phpbb_posts USING btree (forum_id);
CREATE INDEX phpbb_posts_post_username ON phpbb_posts USING btree (post_username);
CREATE INDEX phpbb_posts_post_visibility ON phpbb_posts USING btree (post_visibility);
CREATE INDEX phpbb_posts_poster_id ON phpbb_posts USING btree (poster_id);
CREATE INDEX phpbb_posts_poster_ip ON phpbb_posts USING btree (poster_ip);
CREATE INDEX phpbb_posts_simple_post_content ON phpbb_posts USING gin (to_tsvector('simple'::regconfig, ((post_text || ' '::text) || (post_subject)::text)));
CREATE INDEX phpbb_posts_simple_post_subject ON phpbb_posts USING gin (to_tsvector('simple'::regconfig, (post_subject)::text));
CREATE INDEX phpbb_posts_tid_post_time ON phpbb_posts USING btree (topic_id, post_time);
CREATE INDEX phpbb_posts_topic_id ON phpbb_posts USING btree (topic_id);



