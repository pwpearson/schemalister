drop table public.getschema_fieldusage;

create table if not exists public.getschema_fieldusage(
    id bigserial not null
        constraint getschema_fieldusage
            primary key,
    field_id varchar(10485760),
    type varchar(50),
    name varchar(255)
);

alter table public.getschema_fieldusage owner to postres;
