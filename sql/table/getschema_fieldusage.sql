drop table getschema_fieldusage;

create table if not exists public.getschema_fieldusage
(
	id bigserial not null
		constraint getschema_fieldusage_pk
			primary key,
	field_id bigserial not null,
	type varchar(50),
	name varchar(255)
);

alter table public.getschema_fieldusage owner to postgres;
