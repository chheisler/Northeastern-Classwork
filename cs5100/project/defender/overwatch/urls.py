from django.conf.urls import patterns, url
from overwatch import views

urlpatterns = patterns('',
	url(r'^$', views.label, name='label'),
	url(r'^next/$', views.label_next, name='label_next'),
)