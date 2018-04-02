require 'spec_helper'
describe 'unicloud_tensorflow' do
  context 'with default values for all parameters' do
    it { should contain_class('unicloud_tensorflow') }
  end
end
