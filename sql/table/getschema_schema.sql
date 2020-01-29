create table if not exists public.getschema_schema
(
	id bigserial not null
		constraint getschema_schema_pk
			primary key,
	random_id varchar(1000),
	created_date timestamp,
	finished_date timestamp,
	org_id varchar(1000),
	org_name varchar(1000),
	username varchar(1000),
	access_token varchar(1000),
	instance_url varchar(1000),
	include_field_usage varchar(1000),
	include_managed_objects varchar(1000),
	status varchar(1000),
	error varchar(1000)
);

alter table public.getschema_schema owner to postgres;

