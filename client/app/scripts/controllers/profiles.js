'use strict';

angular.module('miloprofilerApp')

.controller('ProfilesCtrl', ['$scope', '$state', 'Restangular', '$stateParams', function($scope, $state, Restangular, $stateParams) {
    Restangular.all('profiles').getList().then(function(profiles) {
        $scope.profiles = profiles;
      });
    var updateProfile = function(){
          $scope.active = $stateParams.profile;
        };
    $scope.$on('$stateChangeSuccess', updateProfile);
  }])

.directive('profiles', function(){
    return {
        restrict: 'C',
        templateUrl: 'views/navbar.html'
      };
  });
