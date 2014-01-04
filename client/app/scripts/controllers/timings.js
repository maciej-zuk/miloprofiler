'use strict';

angular.module('miloprofilerApp')

.controller('TimingsCtrl', ['$scope', 'Restangular', '$stateParams', function($scope, Restangular, $stateParams) {
    Restangular.one('timings', $stateParams.profile).getList().then(function(timings){
        $scope.timings = timings;
      });
  }])

.controller('TimingDetailsCtrl', ['$scope', 'Restangular', '$stateParams', '$state', function($scope, Restangular, $stateParams, $state) {
    Restangular.one('timings', $stateParams.profile).one($stateParams.id).get().then(function(timing){
        $scope.timing = timing;
      }, function(){
        $state.go('timings', {profile: $stateParams.profile});
      });
  }]);

