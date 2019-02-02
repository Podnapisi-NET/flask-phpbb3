-- A poor man's phpbb3 copy
create table phpbb_users (
    user_id serial primary key,
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
    username
    , username_clean
) values (
    'Anonymous'
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
    group_id  serial  primary key,
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
    auth_option_id  serial  primary key,
    auth_option  character varying(50)  not null default ''::character varying,
    is_global  smallint  not null default (0)::smallint,
    is_local  smallint  not null default (0)::smallint,
    founder_only  smallint  not null default (0)::smallint
);

create table phpbb_notifications (
    notification_id  serial  primary key,
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
