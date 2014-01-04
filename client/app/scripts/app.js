'use strict';

angular.module('miloprofilerApp', [
  'ngCookies',
  'restangular',
  'ngSanitize',
  'ui.route',
  'ui.router',
  'ui.scrollfix',
])
  .config(function($urlRouterProvider, $stateProvider, RestangularProvider){
  $stateProvider
    .state('profiler', {
      url: '/',
      views: {
        'main': { template: 'main' }
      }
    })
    .state('requests', {
      url: '/requests/:profile',
      views: {
        'main': {
          templateUrl: 'views/requests.html',
          controller: 'RequestsCtrl'
        }
      }
    })
    .state('requests.detail', {
      url: '/details/:id',
      views: {
        'details': {
          templateUrl: 'views/requests.details.html',
          controller: 'RequestDetailsCtrl'
        }
      }
    })
    .state('timings', {
      url: '/timings/:profile',
      views: {
        'main': {
          templateUrl: 'views/timings.html',
          controller: 'TimingsCtrl'
        }
      }
    })
    .state('timings.detail', {
      url: '/details/:id',
      views: {
        'details': {
          templateUrl: 'views/timings.details.html',
          controller: 'TimingDetailsCtrl'
        }
      }
    });
  $urlRouterProvider.otherwise('/');
  RestangularProvider.setBaseUrl('http://localhost:5000/');
});
