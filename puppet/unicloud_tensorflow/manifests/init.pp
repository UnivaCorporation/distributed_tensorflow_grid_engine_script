class unicloud_tensorflow {
  ensure_packages(['python2-pip'], {'ensure' => 'installed'})

  # install Tensorflow
  package { 'tensorflow':
    ensure   => '1.2.0rc0',
    provider => 'pip',
    require  => Package['python2-pip'],
  }
}
