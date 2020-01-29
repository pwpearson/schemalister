create table if not exists public.getschema_object
(
	id bigserial not null
		constraint getschema_object_pk
			primary key,
	schema_id bigint,
	label varchar(1000),
	api_name varchar(1000)
);

alter table public.getschema_object owner to postgres;

