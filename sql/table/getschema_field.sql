create table if not exists public.getschema_field
(
	id bigserial not null
		constraint getscheam_field_pk
			primary key,
	object_id bigint,
	label varchar(1000),
	api_name varchar(1000),
	data_type varchar(10485760),
	description varchar(10485760),
	help_text varchar(10485760),
	formula varchar(10485760),
	attributes varchar(10485760),
	field_usage_display varchar(10485760),
	field_usage_display_text varchar(10485760)
);

alter table public.getschema_field owner to postgres;

