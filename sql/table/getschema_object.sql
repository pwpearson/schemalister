drop table getschema_object;

create table if not exists public.getschema_object
(
	id bigserial not null
		constraint getschema_object_pk
			primary key,
	schema_id bigint,
	label varchar(10485760),
	api_name varchar(10485760)
);

alter table public.getschema_object owner to postgres;

